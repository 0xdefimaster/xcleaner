"""XCleaner çekirdeği.

Giriş yapılmış gerçek bir Chromium tabanlı tarayıcıyı (Chrome, Brave, Edge...)
sürer ve X profilindeki *kendi* gönderi/yanıtlarını, elle yapacağın gibi tek
tek siler. Hem CLI (cli.py) hem web arayüzü (server.py) bu modülü kullanır.
"""
from __future__ import annotations

import os
import random
import re
import plistlib
import shutil
import socket
import subprocess
import sys
import threading
from urllib.parse import urlparse
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from selenium import webdriver
from selenium.common.exceptions import (
    InvalidSessionIdException,
    NoSuchElementException,
    NoSuchWindowException,
    StaleElementReferenceException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

LogFn = Callable[[str, str], None]  # (mesaj, "info" | "success" | "error")
CountFn = Callable[[int], None]

USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{1,15}$")
ATTACH_RE = re.compile(r"^[A-Za-z0-9.\-]+:\d{2,5}$")

# Menüdeki "sil" seçeneğini dil bağımsız yakalamak için. X yalnızca kendi
# gönderilerinde bu seçeneği gösterir; asıl güvence budur.
DELETE_WORDS = {
    "delete", "sil", "löschen", "supprimer", "eliminar", "elimina",
    "excluir", "удалить", "削除", "삭제", "حذف",
}

_AUTHOR_JS = """
const a = arguments[0];
const n = a.querySelector('[data-testid="User-Name"] a[href]');
return n ? n.getAttribute('href') : null;
"""


_RESERVED = {"home", "i", "explore", "search", "settings", "notifications",
             "messages", "compose", "login", "logout", "intent", "share", "hashtag"}
_URL_RE = re.compile(r"^(?:https?://)?(?:www\.|mobile\.)?(?:x|twitter)\.com/([^/?#\s]+)", re.IGNORECASE)


def extract_username(value: str) -> str:
    """'@ad', 'ad' veya profil linki (x.com/ad, twitter.com/ad/with_replies?...) -> 'ad'.
    Tanınmazsa girdiyi olduğu gibi (kırpılmış) döndürür; doğrulamayı validate() yapar."""
    v = (value or "").strip()
    m = _URL_RE.match(v)
    if m:
        name = m.group(1)
        return "" if name.lower() in _RESERVED else name
    return v.lstrip("@")


def is_delete_label(text: str) -> bool:
    tokens = re.findall(r"\w+", (text or "").casefold())
    return any(t in DELETE_WORDS for t in tokens)


BROWSER_NAMES = ("brave", "chrome", "edge", "chromium")   # otomatik aramada bu sırayla denenir


def _browser_candidates(name: str) -> list[str]:
    if sys.platform.startswith("win"):
        roots = [os.environ.get(k) for k in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA")]
        rel = {
            "brave": r"BraveSoftware\Brave-Browser\Application\brave.exe",
            "chrome": r"Google\Chrome\Application\chrome.exe",
            "edge": r"Microsoft\Edge\Application\msedge.exe",
            "chromium": r"Chromium\Application\chrome.exe",
        }[name]
        return [os.path.join(r, rel) for r in roots if r]
    if sys.platform == "darwin":
        return [{
            "brave": "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
            "chrome": "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "edge": "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
            "chromium": "/Applications/Chromium.app/Contents/MacOS/Chromium",
        }[name]]
    cmds = {
        "brave": ("brave-browser", "brave"),
        "chrome": ("google-chrome", "google-chrome-stable"),
        "edge": ("microsoft-edge", "microsoft-edge-stable"),
        "chromium": ("chromium", "chromium-browser"),
    }[name]
    return [p for p in (shutil.which(c) for c in cmds) if p]


def _resolve_profile_dir(value: str) -> str:
    """Varsayılan profil klasörü: kaynak koddan çalışırken ./browser_profile;
    paketlenmiş uygulamada (.exe/.app) kullanıcının uygulama verisi klasörü."""
    v = (value or "").strip() or "browser_profile"
    if v == "browser_profile" and getattr(sys, "frozen", False):
        if sys.platform.startswith("win"):
            base = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData/Local")
        elif sys.platform == "darwin":
            base = Path.home() / "Library/Application Support"
        else:
            base = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local/share")
        return str(base / "XCleaner" / "browser_profile")
    return os.path.abspath(v)


def _key_from_id(ident: str) -> Optional[str]:
    """ProgId / bundle id / .desktop adından tarayıcı anahtarı: 'BraveHTML' -> 'brave'.
    Chromium tabanlı olmayanlar (Firefox, Safari...) için None döner."""
    v = (ident or "").lower()
    if "brave" in v:
        return "brave"
    if "edge" in v:
        return "edge"
    if "chromium" in v:
        return "chromium"
    if "chrome" in v:
        return "chrome"
    return None


def _default_browser_id() -> str:
    """İşletim sisteminin varsayılan web tarayıcısının tanımlayıcısını döndürür ('' = bulunamadı)."""
    try:
        if sys.platform.startswith("win"):
            import winreg  # type: ignore
            key = r"Software\Microsoft\Windows\Shell\Associations\UrlAssociations\https\UserChoice"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key) as k:
                return str(winreg.QueryValueEx(k, "ProgId")[0])
        if sys.platform == "darwin":
            plist = Path.home() / "Library/Preferences/com.apple.LaunchServices/com.apple.launchservices.secure.plist"
            with open(plist, "rb") as fh:
                for h in plistlib.load(fh).get("LSHandlers", []):
                    if h.get("LSHandlerURLScheme") == "https":
                        return str(h.get("LSHandlerRoleAll", ""))
            return ""
        for cmd in (["xdg-settings", "get", "default-web-browser"],
                    ["xdg-mime", "query", "default", "x-scheme-handler/https"]):
            if shutil.which(cmd[0]):
                out = subprocess.run(cmd, capture_output=True, text=True, timeout=5).stdout.strip()
                if out:
                    return out
    except Exception:
        pass
    return ""


def find_browser(name: str = "") -> Optional[str]:
    """Kurulu tarayıcının yolunu bulur.
    name: brave|chrome|edge|chromium. Boşsa önce bilgisayarın VARSAYILAN tarayıcısı
    (Chromium tabanlıysa), değilse kurulu olanlar sırayla denenir."""
    if name:
        names = [name.lower()]
    else:
        names = list(BROWSER_NAMES)
        default_key = _key_from_id(_default_browser_id())
        if default_key:
            names.remove(default_key)
            names.insert(0, default_key)
    for n in names:
        for c in _browser_candidates(n):
            if os.path.isfile(c):
                return c
    return None


@dataclass
class Config:
    username: str
    browser_path: str = ""          # boşsa otomatik aranır
    profile_dir: str = "browser_profile"
    attach: str = ""                # "127.0.0.1:9222" -> açık tarayıcıya bağlan
    dry_run: bool = False           # True: hiçbir şey silmeden say
    max_delete: int = 0             # 0 = sınırsız
    min_delay: float = 2.5          # iki silme arası bekleme (sn)
    max_delay: float = 4.5
    stagnant_limit: int = 5         # sayfa sonu sayılması için hareketsiz kaydırma sayısı

    def validate(self) -> None:
        self.username = extract_username(self.username)
        if not USERNAME_RE.match(self.username):
            raise ValueError("Geçersiz kullanıcı adı ya da profil linki (harf, rakam, alt çizgi; en fazla 15 karakter).")
        if self.attach:
            if not ATTACH_RE.match(self.attach):
                raise ValueError("Attach adresi 'host:port' biçiminde olmalı (örn. 127.0.0.1:9222).")
        else:
            bp = self.browser_path.strip()
            if bp.lower() in BROWSER_NAMES:
                found = find_browser(bp.lower())
                if not found:
                    raise ValueError(f"{bp} kurulu görünmüyor. Başka bir tarayıcı seç ya da yolunu elle gir.")
                bp = found
            self.browser_path = bp or find_browser() or ""
            if not os.path.isfile(self.browser_path):
                raise ValueError("Uygun tarayıcı bulunamadı. Brave, Chrome veya Edge kurulu olmalı (Firefox ve Safari desteklenmiyor). İstersen tarayıcı yolunu elle gir.")
            self.profile_dir = _resolve_profile_dir(self.profile_dir)
        if self.max_delete < 0:
            raise ValueError("max_delete negatif olamaz.")
        if self.min_delay < 1.0 or self.max_delay < self.min_delay:
            raise ValueError("Bekleme süresi en az 1 sn olmalı ve max >= min olmalı.")


def _free_local_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sk:
        sk.bind(("127.0.0.1", 0))
        return sk.getsockname()[1]


def _launch_normal_browser(cfg: Config, wait: float = 25.0):
    """Tarayıcıyı Selenium'un otomasyon bayrakları OLMADAN, normal bir pencere olarak açar
    (hata ayıklama portuyla). Böylece 'test yazılımı kontrol ediyor' uyarısı ve Google girişinin
    engellenmesi olmaz. (Popen, adres) döndürür."""
    Path(cfg.profile_dir).mkdir(parents=True, exist_ok=True)
    port = _free_local_port()
    proc = subprocess.Popen(
        [cfg.browser_path, f"--remote-debugging-port={port}", f"--user-data-dir={cfg.profile_dir}",
         "--no-first-run", "--no-default-browser-check", "--window-size=1280,1000", "about:blank"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    deadline = time.time() + wait
    while time.time() < deadline:
        if proc.poll() is not None:
            raise WebDriverException("Tarayıcı hemen kapandı (aynı profili kullanan bir pencere zaten açık olabilir).")
        try:
            socket.create_connection(("127.0.0.1", port), timeout=0.5).close()
            return proc, f"127.0.0.1:{port}"
        except OSError:
            time.sleep(0.3)
    proc.terminate()
    raise WebDriverException("Tarayıcının hata ayıklama portu zamanında açılmadı.")


def _close_launched_browser(driver, proc) -> None:
    """Kendi açtığımız tarayıcıyı düzgünce kapatır (çerezler diske yazılsın diye önce nazikçe)."""
    if driver is not None:
        try:
            driver.execute_cdp_cmd("Browser.close", {})
        except Exception:
            pass
    if proc is not None:
        try:
            proc.wait(timeout=8)
        except Exception:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except Exception:
                proc.kill()


def _make_driver(cfg: Config, address: str) -> webdriver.Chrome:
    """Çalışan bir tarayıcıya bağlanır (otomasyon bayrağı eklemez)."""
    opts = Options()
    opts.debugger_address = address
    if cfg.browser_path and not cfg.attach:
        # Selenium Manager doğru sürücü sürümünü bu tarayıcıdan (ör. Brave) anlasın diye
        opts.binary_location = cfg.browser_path
    # Sürücüyü Selenium Manager (selenium >= 4.11) kendisi bulur/indirir.
    return webdriver.Chrome(options=opts)


def _mark_skip(driver, article) -> None:
    try:
        driver.execute_script("arguments[0].setAttribute('data-xc-skip','1');", article)
    except WebDriverException:
        pass


def _close_menu(driver) -> None:
    try:
        ActionChains(driver).send_keys(Keys.ESCAPE).perform()
    except WebDriverException:
        pass


def _next_article(driver):
    arts = driver.find_elements(
        By.CSS_SELECTOR, '[data-testid="primaryColumn"] article:not([data-xc-skip])'
    )
    return arts[0] if arts else None


def _scroll(driver, stop: threading.Event) -> bool:
    """Aşağı kaydırır; sayfa gerçekten ilerlediyse/uzadıysa True döner."""
    probe = "return [Math.round(window.scrollY), document.documentElement.scrollHeight];"
    before = driver.execute_script(probe)
    driver.execute_script("window.scrollBy(0, Math.max(400, window.innerHeight * 0.8));")
    stop.wait(1.8)
    return driver.execute_script(probe) != before


def _is_logged_in(driver) -> bool:
    """X oturum çerezi (auth_token) varsa giriş yapılmıştır."""
    try:
        return any(c.get("name") == "auth_token" for c in driver.get_cookies())
    except WebDriverException:
        return False


def _wait_for_timeline(driver, cfg: Config, url: str, log: LogFn,
                       stop: threading.Event, timeout: float = 300) -> bool:
    """Giriş yapılmasını ve profil akışının görünmesini bekler.
    Giriş yapılana kadar sayfaya HİÇ dokunmaz (yenileme/yönlendirme yok)."""
    deadline = time.time() + timeout
    told_login = told_wait = False
    last_nav = 0.0
    user_path = "/" + cfg.username.lower()
    while time.time() < deadline and not stop.is_set():
        if not _is_logged_in(driver):
            if not told_login:
                log("Giriş yapılmamış görünüyor. Açılan tarayıcıda X'e giriş yap; "
                    "bu sürede sayfayı yenilemeyeceğim. (En fazla 5 dk beklerim.) "
                    "İpucu: 'Google ile giriş' engellenirse X'in kendi e-posta/kullanıcı adı + şifre girişini kullan.", "info")
                told_login = True
            stop.wait(2)
            continue
        if not told_wait:
            log("Giriş algılandı, profil akışı bekleniyor...", "info")
            told_wait = True
        if driver.find_elements(By.CSS_SELECTOR, '[data-testid="primaryColumn"] article'):
            return True
        path = urlparse(driver.current_url).path.lower()
        if not path.startswith(user_path) and time.time() - last_nav > 8:
            driver.get(url)  # giriş sonrası /home'a düştüyse profile dön (en fazla 8 sn'de bir)
            last_nav = time.time()
        stop.wait(2)
    return False


def _handle_article(driver, art, cfg: Config, stop: threading.Event) -> str:
    """Tek bir gönderiyi işler. 'deleted' | 'dry' | 'skipped' | 'unsure' döner."""
    author = driver.execute_script(_AUTHOR_JS, art)
    if author is not None and author.strip("/").lower() != cfg.username.lower():
        _mark_skip(driver, art)          # başkasının gönderisi: menüyü hiç açma
        return "skipped"

    try:
        caret = art.find_element(By.CSS_SELECTOR, '[data-testid="caret"]')
    except NoSuchElementException:
        _mark_skip(driver, art)
        return "skipped"

    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", caret)
    stop.wait(0.6)
    driver.execute_script("arguments[0].click();", caret)

    try:
        items = WebDriverWait(driver, 4).until(
            lambda d: d.find_elements(By.CSS_SELECTOR, '[role="menuitem"]') or False
        )
    except TimeoutException:
        _close_menu(driver)
        _mark_skip(driver, art)
        return "skipped"

    target = next((i for i in items if is_delete_label(i.text)), None)
    if target is None:
        _close_menu(driver)
        _mark_skip(driver, art)
        return "skipped"
    if cfg.dry_run:
        _close_menu(driver)
        _mark_skip(driver, art)
        return "dry"

    driver.execute_script("arguments[0].click();", target)
    confirm = WebDriverWait(driver, 6).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="confirmationSheetConfirm"]'))
    )
    confirm.click()
    try:
        WebDriverWait(driver, 6).until(EC.staleness_of(art))
    except TimeoutException:
        _mark_skip(driver, art)          # yerinde kaldıysa sonsuza dek denemesin
        return "unsure"
    return "deleted"


def run(cfg: Config, log: LogFn, on_count: Optional[CountFn] = None,
        stop: Optional[threading.Event] = None) -> dict:
    """Temizliği çalıştırır. {'deleted', 'would_delete', 'reason'} döner."""
    cfg.validate()
    stop = stop or threading.Event()
    on_count = on_count or (lambda n: None)
    result = {"deleted": 0, "would_delete": 0, "reason": ""}
    url = f"https://x.com/{cfg.username}/with_replies"
    driver = None
    proc = None

    try:
        log(f"Tarayıcı başlatılıyor: {cfg.browser_path or cfg.attach}", "info")
        try:
            if cfg.attach:
                address = cfg.attach
            else:
                proc, address = _launch_normal_browser(cfg)
            driver = _make_driver(cfg, address)
        except WebDriverException as exc:
            result["reason"] = "browser_start_failed"
            _close_launched_browser(None, proc)
            detail = (getattr(exc, "msg", "") or str(exc)).strip().splitlines()[0][:200] if str(exc).strip() else type(exc).__name__
            log(f"Tarayıcı başlatılamadı: {detail}. Bu programın açtığı eski bir tarayıcı penceresi kaldıysa "
                "kapat ve tekrar dene. Tarayıcının kendi günlük profilini (User Data) profil olarak verme: "
                "yeni Chrome/Edge/Brave sürümleri otomasyonu varsayılan profilde engelliyor.", "error")
            return result
        driver.get(url)
        if not _wait_for_timeline(driver, cfg, url, log, stop):
            result["reason"] = "stopped" if stop.is_set() else "timeline_not_found"
            if not stop.is_set():
                log("Zaman çizelgesi bulunamadı (giriş yapılmamış ya da profil boş olabilir).", "error")
            return result
        log("Zaman çizelgesi hazır." + (" DENEME MODU: hiçbir şey silinmeyecek." if cfg.dry_run else ""), "success")

        stagnant = refreshes = errors = 0
        while not stop.is_set():
            done = result["would_delete"] if cfg.dry_run else result["deleted"]
            if cfg.max_delete and done >= cfg.max_delete:
                result["reason"] = "max_reached"
                log(f"Üst sınıra ulaşıldı ({cfg.max_delete}).", "info")
                break

            art = _next_article(driver)
            if art is None:
                stagnant = 0 if _scroll(driver, stop) else stagnant + 1
                if stagnant >= cfg.stagnant_limit:
                    if cfg.dry_run or refreshes >= 2:
                        result["reason"] = "finished"
                        log("Akışın sonuna ulaşıldı.", "info")
                        break
                    refreshes += 1
                    log(f"Akışın sonu göründü, kalan var mı diye sayfa yenileniyor ({refreshes}/2)...", "info")
                    driver.refresh()
                    _wait_for_timeline(driver, cfg, url, log, stop, timeout=60)
                    stagnant = 0
                continue

            try:
                outcome = _handle_article(driver, art, cfg, stop)
                errors = 0
            except StaleElementReferenceException:
                continue
            except (NoSuchWindowException, InvalidSessionIdException):
                result["reason"] = "browser_closed"
                log("Tarayıcı kapatıldı, işlem durduruldu.", "error")
                break
            except WebDriverException as exc:
                errors += 1
                log(f"Bir gönderi atlandı: {type(exc).__name__}", "error")
                _close_menu(driver)
                _mark_skip(driver, art)
                if errors >= 5:
                    result["reason"] = "too_many_errors"
                    log("Üst üste 5 hata: X arayüzü değişmiş olabilir. Durduruluyor.", "error")
                    break
                continue

            if outcome == "deleted":
                result["deleted"] += 1
                stagnant = refreshes = 0
                on_count(result["deleted"])
                log(f"Silindi. Toplam: {result['deleted']}", "success")
                stop.wait(random.uniform(cfg.min_delay, cfg.max_delay))
            elif outcome == "dry":
                result["would_delete"] += 1
                on_count(result["would_delete"])
                log(f"[deneme] Silinebilir gönderi #{result['would_delete']}", "success")
            elif outcome == "unsure":
                log("Silme onaylandı ama gönderi yerinde kaldı; atlanıyor.", "error")

        if stop.is_set() and not result["reason"]:
            result["reason"] = "stopped"

        total = result["would_delete"] if cfg.dry_run else result["deleted"]
        verb = "silinebilir" if cfg.dry_run else "silindi"
        log(f"Bitti: {total} gönderi {verb}.", "success" if total else "info")
        if total == 0 and result["reason"] == "finished":
            log("Hiçbir şey bulunamadı. Doğru hesapla giriş yaptığından emin ol.", "info")
        return result

    finally:
        if driver is not None:
            try:
                if cfg.attach:
                    driver.service.stop()   # kullanıcının tarayıcısını kapatma
                else:
                    _close_launched_browser(driver, proc)   # kendi açtığımız pencereyi kapat
                    driver.service.stop()
            except Exception:
                pass
        elif proc is not None:
            _close_launched_browser(None, proc)

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import cleaner  # noqa: E402
from cleaner import Config, extract_username, is_delete_label  # noqa: E402


@pytest.mark.parametrize("text", ["Delete", "Gönderiyi sil", "Sil", "Löschen", "Supprimer le post"])
def test_delete_labels_match(text):
    assert is_delete_label(text)


@pytest.mark.parametrize("text", ["", "Sessize al", "Mute @someone", "Follow @someone", "Bu gönderiyi bildir"])
def test_other_menu_items_do_not_match(text):
    assert not is_delete_label(text)


def _cfg(tmp_path, **kw):
    browser = tmp_path / "browser"
    browser.write_text("")
    return Config(username="kullanici", browser_path=str(browser), profile_dir=str(tmp_path / "p"), **kw)


def test_validate_strips_at_sign(tmp_path):
    cfg = _cfg(tmp_path)
    cfg.username = "@kullanici"
    cfg.validate()
    assert cfg.username == "kullanici"


@pytest.mark.parametrize("name", ["", "a b", "way_too_long_username_here", "x/../y", "a;b"])
def test_validate_rejects_bad_usernames(tmp_path, name):
    cfg = _cfg(tmp_path)
    cfg.username = name
    with pytest.raises(ValueError):
        cfg.validate()


def test_validate_rejects_missing_browser(tmp_path):
    cfg = Config(username="kullanici", browser_path=str(tmp_path / "yok"))
    with pytest.raises(ValueError):
        cfg.validate()


def test_validate_delay_bounds(tmp_path):
    with pytest.raises(ValueError):
        _cfg(tmp_path, min_delay=0.2).validate()
    with pytest.raises(ValueError):
        _cfg(tmp_path, min_delay=5, max_delay=3).validate()


def test_validate_attach_format(tmp_path):
    Config(username="kullanici", attach="127.0.0.1:9222").validate()
    with pytest.raises(ValueError):
        Config(username="kullanici", attach="127.0.0.1; rm -rf").validate()


@pytest.mark.parametrize("value,expected", [
    ("https://x.com/gasdaoooaqs", "gasdaoooaqs"),
    ("http://www.twitter.com/Abc_1/with_replies?s=20", "Abc_1"),
    ("x.com/abc/", "abc"),
    ("@abc", "abc"),
    ("abc", "abc"),
    ("https://x.com/home", ""),
    ("https://x.com/i/flow/login", ""),
])
def test_extract_username(value, expected):
    assert extract_username(value) == expected


def test_validate_accepts_profile_url(tmp_path):
    cfg = _cfg(tmp_path)
    cfg.username = "https://x.com/gasdaoooaqs"
    cfg.validate()
    assert cfg.username == "gasdaoooaqs"


def test_browser_name_is_resolved(tmp_path, monkeypatch):
    exe = tmp_path / "brave"
    exe.write_text("")
    monkeypatch.setattr(cleaner, "find_browser", lambda name="": str(exe) if name in ("", "brave") else None)
    cfg = Config(username="kullanici", browser_path="Brave", profile_dir=str(tmp_path / "p"))
    cfg.validate()
    assert cfg.browser_path == str(exe)


def test_browser_name_not_installed(tmp_path, monkeypatch):
    monkeypatch.setattr(cleaner, "find_browser", lambda name="": None)
    with pytest.raises(ValueError):
        Config(username="kullanici", browser_path="edge").validate()


class _FakeDriver:
    def __init__(self, cookies, url="https://x.com/"):
        self._cookies, self.current_url, self.gets = cookies, url, []

    def get_cookies(self):
        return self._cookies

    def find_elements(self, *a, **k):
        return []

    def get(self, url):
        self.gets.append(url)


def test_is_logged_in():
    assert cleaner._is_logged_in(_FakeDriver([{"name": "auth_token"}]))
    assert not cleaner._is_logged_in(_FakeDriver([{"name": "guest_id"}]))


def test_wait_does_not_touch_page_while_logged_out():
    import threading
    drv = _FakeDriver([], url="https://x.com/")
    logs = []
    cfg = Config(username="kullanici")
    ok = cleaner._wait_for_timeline(drv, cfg, "https://x.com/kullanici/with_replies",
                                    lambda m, lvl="info": logs.append(m), threading.Event(), timeout=0.1)
    assert ok is False
    assert drv.gets == []          # sayfa yenilenmedi / yönlendirilmedi
    assert any("Giriş yapılmamış" in m for m in logs)


@pytest.mark.parametrize("ident,expected", [
    ("BraveHTML", "brave"), ("ChromeHTML", "chrome"), ("MSEdgeHTM", "edge"),
    ("com.brave.Browser", "brave"), ("com.google.Chrome", "chrome"),
    ("com.microsoft.edgemac", "edge"), ("org.chromium.Chromium", "chromium"),
    ("brave-browser.desktop", "brave"), ("google-chrome.desktop", "chrome"),
    ("microsoft-edge.desktop", "edge"), ("chromium.desktop", "chromium"),
    ("FirefoxURL-308046B0AF4A39CB", None), ("com.apple.safari", None), ("", None),
])
def test_key_from_id(ident, expected):
    assert cleaner._key_from_id(ident) == expected


def test_find_browser_prefers_default(tmp_path, monkeypatch):
    brave, chrome = tmp_path / "brave", tmp_path / "chrome"
    brave.write_text(""); chrome.write_text("")
    monkeypatch.setattr(cleaner, "_browser_candidates",
                        lambda n: [str(brave)] if n == "brave" else [str(chrome)] if n == "chrome" else [])
    monkeypatch.setattr(cleaner, "_default_browser_id", lambda: "ChromeHTML")
    assert cleaner.find_browser() == str(chrome)          # varsayılan Chrome -> Brave'den önce
    monkeypatch.setattr(cleaner, "_default_browser_id", lambda: "FirefoxURL-1")
    assert cleaner.find_browser() == str(brave)           # desteklenmiyorsa sıradaki kurulu olan
    monkeypatch.setattr(cleaner, "_default_browser_id", lambda: "")
    assert cleaner.find_browser() == str(brave)


@pytest.mark.skipif(sys.platform.startswith("win"), reason="sahte tarayıcı betiği POSIX'e özel")
def test_launch_normal_browser_opens_debug_port(tmp_path):
    fake = tmp_path / "fakebrowser"
    fake.write_text(
        "#!/bin/sh\n"
        'for a in "$@"; do case "$a" in --remote-debugging-port=*) P="${a#*=}";; esac; done\n'
        f'exec {sys.executable} -c "import socket,sys,time;s=socket.socket();'
        "s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);s.bind(('127.0.0.1',int(sys.argv[1])));"
        's.listen(5);time.sleep(30)" "$P"\n'
    )
    fake.chmod(0o755)
    cfg = Config(username="kullanici", browser_path=str(fake), profile_dir=str(tmp_path / "prof"))
    cfg.validate()
    proc, addr = cleaner._launch_normal_browser(cfg, wait=10)
    try:
        assert addr.startswith("127.0.0.1:")
        assert (tmp_path / "prof").is_dir()
    finally:
        cleaner._close_launched_browser(None, proc)
    assert proc.poll() is not None


@pytest.mark.skipif(sys.platform.startswith("win"), reason="sahte tarayıcı betiği POSIX'e özel")
def test_launch_normal_browser_reports_immediate_exit(tmp_path):
    fake = tmp_path / "fakebrowser"
    fake.write_text("#!/bin/sh\nexit 0\n")
    fake.chmod(0o755)
    cfg = Config(username="kullanici", browser_path=str(fake), profile_dir=str(tmp_path / "prof"))
    cfg.validate()
    with pytest.raises(cleaner.WebDriverException):
        cleaner._launch_normal_browser(cfg, wait=5)

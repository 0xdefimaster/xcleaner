# XCleaner

X (Twitter) hesabındaki **kendi** gönderi ve yanıtlarını toplu silen küçük bir araç. Giriş yapılmış gerçek bir tarayıcıyı (Brave, Chrome, Edge) Selenium ile sürer; profilindeki gönderilere tek tek gidip elle yapacağın gibi "Sil" der. **API anahtarı, geliştirici hesabı veya şifre paylaşımı gerekmez.**

[English](#english) · [Kurulum](#kurulum) · [Kullanım](#kullanım) · [Sorun giderme](#sorun-giderme) · [SSS](#sık-sorulan-sorular)

---

## Önce oku

- **Silme kalıcıdır.** Geri getirmenin yolu yok. İlk çalıştırmada mutlaka **Deneme modunu** (`--dry-run`) kullan.
- Silmeden önce arşivini indir: X → Ayarlar → Hesabın → Verilerinin arşivini indir.
- Araç yalnızca **kendi hesabında** çalışır. Başkasının gönderisinde "Sil" seçeneği çıkmaz ve araç o gönderilere hiç dokunmaz.
- Otomasyon X'in kullanım koşullarıyla çelişebilir, sorumluluk sende. Hız sınırına ya da geçici kısıtlamaya takılmamak için bekleme sürelerini kısmadan kullan (silmeler arası en az 1 sn zorunludur).
- **Yalnızca gönderi ve yanıtlar silinir.** Beğeniler ve repost'lar geri alınmaz.
- X arayüzü değişirse araç çalışmayabilir. Bkz. [Sorun giderme](#sorun-giderme).

## Nasıl çalışır?

1. Tarayıcıyı ayrı bir profille, normal bir pencere olarak açar (Selenium'un otomasyon bayrakları olmadan), ona bağlanır ve `x.com/<kullanıcı>/with_replies` sayfasına gider.
2. Ekrandaki her gönderinin yazarına bakar. Yazar sen değilsen menüyü hiç açmaz.
3. Kendi gönderinde üç nokta menüsünü açar, "Sil / Delete" seçeneğini bulur (TR, EN, DE, FR, ES, PT, RU, JA, KO, AR), onay penceresini onaylar ve gönderinin gerçekten kaybolduğunu doğrular.
4. İşlenecek gönderi kalmayınca aşağı kaydırır. Akışın sonuna gelince sayfayı en fazla iki kez yenileyip kalan var mı diye bakar, yoksa biter.

Hiçbir veri dışarı gönderilmez. Araç yalnızca `x.com` ile, senin açtığın tarayıcı üzerinden konuşur. Varsayılan tarayıcıyı bulmak için yalnızca işletim sisteminin ayarı okunur (Windows kayıt defteri, macOS ayar dosyası, Linux `xdg-settings`); başka bir şey çalıştırılmaz.

## Kurulum

Programcı olmana gerek yok. Aşağıdaki üç yoldan sana uyanı seç.

### Yol A: İndir ve çift tıkla (önerilen)

1. [**Releases**](../../releases/latest) sayfasını aç, "Assets" bölümünden bilgisayarına uygun dosyayı indir:

   | Bilgisayarın | İndirilecek dosya |
   |---|---|
   | Windows 10 / 11 | `XCleaner-windows.exe` |
   | Mac (Apple işlemcili: M1, M2, M3...) | `XCleaner-macos` |
   | Linux | `XCleaner-linux` |

   > Intel işlemcili eski bir Mac'in varsa `XCleaner-macos` çalışmaz; onun yerine aşağıdaki **Yol B**'yi kullan. Hangisine sahip olduğunu bilmiyorsan: Apple menüsü → "Bu Mac Hakkında".
2. Dosyaya çift tıkla. Python kurmana gerek yok.
3. Nasıl kullanacağın için aşağıdaki **[Adım adım: ilk kullanım](#adım-adım-ilk-kullanım)** bölümüne bak.

> **Windows "SmartScreen: Bilinmeyen yayımcı" uyarısı verirse:** "Ek bilgi" → "Yine de çalıştır". Program imzalı olmadığı için bu uyarı çıkar; kaynak kodu bu repoda açık ve dosyayı GitHub Actions kendi derliyor.
> **macOS'ta "açılamıyor" derse:** dosyaya sağ tıkla → "Aç" → "Aç". Gerekirse Terminal'de `chmod +x XCleaner-macos` yaz.

### Yol B: Python varsa, kaynak koddan çift tıkla

Repoyu **Code → Download ZIP** ile indirip klasöre çıkar, sonra:

| Sistem | Ne yapılır |
|---|---|
| Windows | `start.bat` dosyasına çift tıkla |
| macOS | `start.command` dosyasına çift tıkla (ilk seferde sağ tık → Aç) |
| Linux | `./start.sh` |

İlk açılışta gerekli paketleri kendisi kurar (birkaç dakika), sonraki açılışlar hızlıdır. Python yoksa Windows'ta indirme sayfasını açar. Kurulumda **"Add python.exe to PATH"** kutusunu işaretle.

### Yol C: Geliştiriciler için

```bash
git clone https://github.com/<kullanici>/xcleaner.git
cd xcleaner

python -m venv .venv
# Windows (PowerShell):  .venv\Scripts\Activate.ps1
# Windows (cmd):         .venv\Scripts\activate.bat
# macOS / Linux:         source .venv/bin/activate

pip install -r requirements.txt
python server.py          # web arayüzü
python cli.py --help      # komut satırı
```

**Gereksinimler:** Chromium tabanlı bir tarayıcı (Brave, Chrome veya Edge; Firefox/Safari desteklenmez). Python yalnızca Yol B ve C için gerekir (3.9+). Tarayıcı sürücüsü (chromedriver) Selenium tarafından otomatik indirilir.

## Adım adım: ilk kullanım

Programı indirdin ve çift tıkladın. Şimdi ne olacak, ne yapacaksın:

**1. Program açılır (ilk seferde 10-30 sn sürebilir).**
Siyah bir pencere (buna "konsol" denir) ve birkaç saniye sonra tarayıcında **XCleaner** sayfası belirir. Siyah pencere programın kendisidir; **kapatma**, işin bitene kadar açık kalsın. Sayfa kendiliğinden açılmazsa siyah pencerede yazan adresi (`http://127.0.0.1:8000` gibi) tarayıcının adres çubuğuna yapıştır.

**2. Formu doldur.**

| Alan | Ne yazacaksın |
|---|---|
| **X kullanıcı adın veya profil linki** | Profilinin linkini yapıştır (ör. `https://x.com/kullanici_adin`) ya da sadece kullanıcı adını yaz. |
| **Hangi tarayıcı?** | Değiştirme. "Otomatik" bilgisayarındaki varsayılan tarayıcıyı bulur (Brave, Chrome veya Edge olmalı; Firefox/Safari desteklenmez). |
| Özel tarayıcı yolu, Profil klasörü | **Boş bırak.** |
| Gelişmiş → En fazla kaç gönderi | İlk denemede `20` yaz; sonra `0` (sınırsız) yaparsın. |
| **Deneme modu** | **İşaretli kalsın.** İşaretliyken hiçbir şey silinmez, sadece sayılır. |

**3. "Başlat" düğmesine bas.**
Yeni bir tarayıcı penceresi açılır. Bu, programın kendi penceresidir; **senin normal tarayıcı pencerelerinden ayrıdır** ve içinde X'e giriş yapılmamıştır.

**4. Açılan pencerede X'e giriş yap (sadece ilk seferde).**
Kullanıcı adın ve şifrenle kendin giriş yap. Şifreni programa yazmıyorsun, X'in kendi sayfasına yazıyorsun. X "yeni cihazdan giriş" diye e-posta veya telefon kodu isteyebilir; bunu tamamla. Giriş yapana kadar program bekler ve sayfaya dokunmaz (5 dakikaya kadar). Giriş sonraki açılışlarda hatırlanır.

> **Neden yeniden giriş yapıyorum?** Program senin günlük tarayıcı profilini kullanamaz: Chrome 136'dan beri Chrome, Edge ve Brave, otomasyona kendi *varsayılan* profilini kapatıyor (güvenlik önlemi). Bu yüzden program ayrı, boş bir profille açılır. Bu giriş **bir kere** yapılır ve o profilde kalır. Günlük tarayıcındaki oturumuna dokunulmaz.
>
> **"Google ile giriş" çalışmıyorsa:** Google giriş ekranı bazen bu pencerede "Oturumunuz açılamadı, bu tarayıcı güvenli olmayabilir" diyebilir. O durumda X'in kendi giriş kutusundan **kullanıcı adı/e-posta + şifre** ile gir. Hesabını Google ile açtıysan ve şifren yoksa, giriş ekranında "Şifreni mi unuttun?" ile e-postana gelen bağlantıdan bir şifre belirle.

**5. Deneme sonucunu oku.**
Giriş yapınca program profiline gidip gönderileri tek tek sayar. Sayfadaki siyah kutuda ilerleme, altındaki büyük sayıda bulunan gönderi sayısı görünür. "Bitti: N gönderi silinebilir" yazınca iş biter. Sayı beklediğine yakınsa devam et.

**6. Gerçekten silmek için:**
- **Deneme modu** kutusunun işaretini kaldır, sonra **Başlat**'a bas.
- Çıkan onay penceresinde hesabın adını kontrol et ve onayla. **Bu adımdan sonrası geri alınamaz.**
- Program gönderileri birer birer, aralarında bekleyerek siler. Bu bilerek yavaştır, X'in hız sınırına takılmamak için.

**7. Bitince.**
"Bitti: N gönderi silindi" yazar. Programı kapatmak için siyah pencereyi kapat. Erken durdurmak istersen sayfadaki **Durdur** düğmesine bas.

**İş sürerken şunlara dikkat et:**
- Programın açtığı tarayıcı penceresini **kapatma** ve içinde tıklama yapma; işi bozar.
- Bilgisayarı uyku moduna almasın (çok gönderin varsa bu birkaç saat sürebilir).
- Yarıda kalırsa sorun değil: programı yeniden başlat. Silinmiş gönderiler zaten görünmez, kalanları silmeye devam eder.

**Başına ne gelebilir?**

| Ne görüyorsun | Ne yapmalısın |
|---|---|
| Windows "bilgisayarını korudu / Bilinmeyen yayımcı" | "Ek bilgi" → "Yine de çalıştır" |
| macOS "açılamıyor, doğrulanamadı" | Dosyaya sağ tık → "Aç" → "Aç" |
| "Uygun tarayıcı bulunamadı" | Brave, Chrome veya Edge kur ve tekrar dene |
| Giriş sayfasında takılı kaldı | Giriş yapmayı tamamla; 5 dk geçtiyse "Durdur" → tekrar "Başlat" |
| "Hiçbir şey bulunamadı" | Yanlış hesapla girişlisin ya da silinecek gönderi kalmadı |
| Sayfa hiç açılmadı | Siyah penceredeki adresi tarayıcına elle yapıştır |
| "Google ile giriş" → "Oturumunuz açılamadı / tarayıcı güvenli olmayabilir" | X'in kendi kullanıcı adı/e-posta + şifre girişini kullan (şifren yoksa "Şifreni mi unuttun?") |
| Pencerenin üstünde "test yazılımı tarafından kontrol ediliyor" yazıyor | Eski sürümdesin; güncel sürümde program tarayıcıyı normal açıp ona bağlanır ve bu uyarı çıkmaz |
| "Tarayıcı hemen kapandı" / "hata ayıklama portu açılmadı" | Programın daha önce açtığı bir tarayıcı penceresi açık kalmış; kapatıp yeniden başlat |

Daha fazla çözüm için aşağıdaki [Sorun giderme](#sorun-giderme) bölümüne bak.

## Kullanım

İki yol var, ikisi de aynı işi yapar. Terminal kullanmayı sevmiyorsan web arayüzünü seç.

### Yol 1: Web arayüzü (kolay)

Adımlar yukarıdaki **[Adım adım: ilk kullanım](#adım-adım-ilk-kullanım)** bölümünde. Programı açmak için indirdiğin dosyayı ya da `start.bat` / `start.command` dosyasını çalıştırman yeterli (geliştiriciler: `python server.py`).

Sunucu yalnızca kendi bilgisayarında (`127.0.0.1`) dinler. Port doluysa bir sonrakine geçer. Farklı port için: `python server.py --port 9000`, tarayıcıyı otomatik açmamak için `--no-browser`.

### Yol 2: Komut satırı

```bash
# 1) Önce silmeden say
python cli.py kullanici_adi --dry-run
# Profil linkini olduğu gibi de verebilirsin
python cli.py https://x.com/kullanici_adi --dry-run

# 2) Gerçekten sil (onay sorar, "evet" yazman gerekir)
python cli.py kullanici_adi

# 3) Sadece ilk 50 gönderiyi sil, daha yavaş git
python cli.py kullanici_adi --max 50 --delay-min 4 --delay-max 8
```

Çalışırken **Ctrl+C** ile güvenle durdurabilirsin.

| Seçenek | Anlamı | Varsayılan |
|---|---|---|
| `username` | X kullanıcı adın ya da profil linkin (zorunlu) | – |
| `--dry-run` | Hiçbir şey silme, sadece say | kapalı |
| `--max N` | En fazla N gönderi sil (0 = sınırsız) | `0` |
| `--delay-min` / `--delay-max` | İki silme arası bekleme (sn, en az 1) | `2.5` / `4.5` |
| `--browser` | `brave`, `chrome`, `edge`, `chromium` ya da .exe yolu | varsayılan tarayıcın |
| `--profile KLASÖR` | Tarayıcı profil klasörü | `./browser_profile` |
| `--attach HOST:PORT` | Açık bir tarayıcıya bağlan (gelişmiş) | – |
| `--yes` | Onay sorusunu atla | kapalı |

Hiçbir şey vermezsen araç varsayılan tarayıcını kullanır (Chrome/Edge/Brave/Chromium ise; Firefox ve Safari desteklenmez, bu durumda kurulu olan ilk Chromium tabanlı tarayıcı seçilir). İstersen adıyla seçebilirsin: `--browser brave`, `--browser chrome`, `--browser edge`. Bulunamazsa tam yolu ver: `--browser "C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"` veya `XCLEANER_BROWSER` ortam değişkenini ayarla.

### Örnek çıktı

```text
[info] Tarayıcı başlatılıyor...
[info] Zaman çizelgesi bekleniyor. Giriş gerekiyorsa açılan tarayıcıda giriş yap.
[success] Zaman çizelgesi hazır. DENEME MODU: hiçbir şey silinmeyecek.
[success] [deneme] Silinebilir gönderi #1
[success] [deneme] Silinebilir gönderi #2
...
[info] Akışın sonuna ulaşıldı.
[success] Bitti: 137 gönderi silinebilir.
```

## İlk çalıştırma ve giriş

Varsayılan olarak araç ayrı bir `browser_profile/` klasörü kullanır (kaynak koddan çalışırken proje klasöründe, indirilen programda `%LOCALAPPDATA%\\XCleaner` / `~/Library/Application Support/XCleaner` / `~/.local/share/XCleaner` altında); günlük tarayıcı profiline dokunmaz.

1. İlk çalıştırmada açılan pencerede X'e **kendin giriş yap** (şifreni araca vermezsin).
2. Araç profil akışı görünene kadar en fazla 5 dakika bekler.
3. Oturum profilde kalır, sonraki çalıştırmalarda tekrar giriş gerekmez.

> `browser_profile/` klasörü oturum bilgisi (çerezler) içerir. `.gitignore` bunu repodan dışarıda tutar; yine de asla paylaşma, zip'leyip gönderme.

> **Neden günlük tarayıcımdaki açık oturumu kullanamıyor?** Chrome 136'dan beri Chrome ve Chromium tabanlı tarayıcılar, otomasyon için gereken uzaktan hata ayıklamayı tarayıcının *varsayılan* profilinde reddediyor ([Chrome duyurusu](https://developer.chrome.com/blog/remote-debugging-port)). Bu yüzden araç kendi `browser_profile/` klasörünü kullanır ve X'e orada **bir kez** giriş yapman gerekir. Sonra oturum kalır.

**Alternatifler**

- **Başka bir profil klasörü ver:** `--profile "D:\baska_profil"`. Aynı klasörü kullanan tüm pencereler kapalı olmalı. Tarayıcının kendi `User Data` klasörünü vermeyi deneme, yukarıdaki nedenle açılmayabilir.
- **Açık tarayıcıya bağlan (gelişmiş):** tarayıcıyı `--remote-debugging-port=9222 --user-data-dir=./browser_profile` ile kendin başlat, giriş yap, sonra `--attach 127.0.0.1:9222` ver. Chrome ile önerilir; Brave gibi tarayıcılarda sürücü sürümü uyuşmayabilir. Bu modda işlem bitince tarayıcın kapatılmaz.

## Önerilen adımlar (özet)

1. X'ten arşivini indir.
2. `--dry-run` ile say, sayı beklediğine yakın mı bak.
3. `--max 20` ile küçük bir deneme yap, hesabında kontrol et.
4. Sonra sınırsız çalıştır. Çok fazla gönderin varsa günlere böl.

## Sorun giderme

| Belirti | Çözüm |
|---|---|
| "Uygun tarayıcı bulunamadı" | `--browser` ile yolu ver (web arayüzünde "Tarayıcı yolu" alanı) |
| Tarayıcı açılıp hemen kapanıyor | Aynı profili kullanan başka pencere açık; kapat ya da başka `--profile` ver |
| "Zaman çizelgesi bulunamadı" | Giriş yapılmamış ya da kullanıcı adı yanlış; açılan pencerede giriş yap |
| Hiç silmiyor, "Hiçbir şey bulunamadı" | Yanlış hesapla girişlisin ya da silinecek gönderi kalmadı |
| "Üst üste 5 hata" / hep atlıyor | X arayüzü değişmiş olabilir; aşağıya bak |
| Silme sonrası "gönderi yerinde kaldı" | Ağ yavaş olabilir ya da X hata verdi; `--delay-min` değerini artırıp yeniden dene |
| Çok sayıda gönderi kaldı ama durdu | X yeni gönderileri yüklemeyi kesmiş olabilir; aracı yeniden çalıştır |

**X arayüzü değiştiyse:** Seçiciler `cleaner.py` içinde `data-testid` değerleri olarak toplu durur (`caret`, `confirmationSheetConfirm`, `primaryColumn`, `User-Name`). Tarayıcıda F12 ile ilgili öğeyi incele, değer değişmişse burada güncelle. Bulduğun düzeltmeyi PR olarak göndermen çok işe yarar.

## Sık sorulan sorular

**Şifremi ya da hesabımı çalar mı?** Hayır. Şifre sorulmaz; girişi kendi açtığın tarayıcıda sen yaparsın. Kod açık, dış sunucuya bağlantı yok.

**Hesabım banlanır mı?** Garanti veremem. Otomasyon X koşullarına aykırı olabilir. Yavaş çalışmak ve büyük işleri parçalamak riski azaltır, sıfırlamaz.

**Başkasının gönderisini silebilir mi?** Hayır. Yazar kontrolü yapar ve X zaten başkasının gönderisinde "Sil" seçeneği göstermez.

**Repost'ları ve beğenileri de silebilir mi?** Şimdilik hayır, yalnızca gönderi ve yanıtlar.

**Belirli bir tarihe kadar olanları silebilir mi?** Şimdilik hayır. `--max` ile sayıyı sınırlayabilirsin. Katkı bekleniyor.

**Mac / Linux'ta çalışır mı?** Evet; Windows, macOS ve Linux'ta tarayıcı otomatik aranır.

## Testler

```bash
pip install -r requirements-dev.txt
pytest
```

Testler doğrulama mantığını ve sunucunun `Origin` kontrolünü kapsar. Gerçek X sayfasına karşı otomatik test yoktur.

## Katkı

Hata bildirimi ve PR'lar açık. X arayüzü değişikliği nedeniyle bir sorun bildirirken lütfen araç çıktısını ve tarayıcı sürümünü ekle.

## Lisans

MIT, bkz. [LICENSE](LICENSE).

---

## English

**XCleaner** bulk-deletes **your own** posts and replies on X (Twitter) by driving a real, logged-in Chromium browser (Brave, Chrome, Edge) with Selenium. It goes through your profile and clicks "Delete" exactly like you would by hand. No API key, no developer account, and it never asks for your password.

### Read first

- **Deletion is permanent.** Always try `--dry-run` first.
- Download your archive before deleting: X → Settings → Your account → Download an archive of your data.
- Only your own posts have a Delete option; the tool also skips any post whose author isn't you.
- Automating X may violate its Terms of Service; use at your own risk. A minimum delay of 1 s between deletions is enforced (default 2.5–4.5 s).
- Only posts and replies are removed. Likes and reposts are **not** undone.
- The tool relies on X's current `data-testid` selectors, which may change over time.

### Install

No programming knowledge needed:

- **Easiest:** download `XCleaner-windows.exe` / `XCleaner-macos` / `XCleaner-linux` from the [Releases](../../releases/latest) page and double-click it. (Windows SmartScreen may warn about an unknown publisher because the file is unsigned: "More info" → "Run anyway". On macOS: right-click → Open.)
- **With Python installed:** download the ZIP and double-click `start.bat` (Windows) / `start.command` (macOS) / `./start.sh` (Linux). It sets everything up on first run.
- **Developers:** `git clone`, create a venv, `pip install -r requirements.txt`, `python server.py`.

You need a Chromium-based browser (Brave, Chrome or Edge); Firefox/Safari are not supported. The driver is fetched automatically by Selenium.

### Quick start (downloaded app)

1. **Open it:** double-click the file. A black window (the program itself, keep it open) appears, then the XCleaner page opens in your browser (first launch can take 10-30 s). If it doesn't, paste the address shown in the black window into your browser.
2. **Fill in the form:** paste your profile link (`https://x.com/your_name`) or username. Leave *Which browser?* on "Auto" and leave the path/profile fields empty. Under *Advanced* set the max to `20` for a first try. Keep **Dry run** checked.
3. **Press Start.** A separate browser window opens, not logged in to X. **Log in there yourself (first time only)**; complete any verification X asks for. The tool waits up to 5 minutes and doesn't touch the page until you're logged in.
4. **Read the dry-run result** ("N posts can be deleted"). If it looks right, **uncheck Dry run**, press Start again and confirm the account name in the popup. This is irreversible.
5. **While it runs:** don't close or click in the window it opened, and keep the computer awake. Press **Stop** any time. Close the black window to quit.

### Usage

**Web UI (easiest)**

Run the downloaded app (or `start.bat`/`start.command`, or `python server.py`). The UI opens in your browser. Enter your username or paste your profile link (`https://x.com/your_username`), keep **Dry run** checked, and press Start. Log in to X in the browser window that opens (first run only). If the count looks right, reload the page, uncheck Dry run, and run again. The server listens on localhost only.

**Command line**

```bash
python cli.py your_username --dry-run              # count only
python cli.py your_username                        # delete (asks for confirmation)
python cli.py your_username --max 50 --delay-min 4 --delay-max 8
```

| Option | Meaning | Default |
|---|---|---|
| `--dry-run` | Don't delete, just count | off |
| `--max N` | Delete at most N posts (0 = unlimited) | `0` |
| `--delay-min` / `--delay-max` | Seconds between deletions (min 1) | `2.5` / `4.5` |
| `--browser` | `brave`, `chrome`, `edge`, `chromium`, or an executable path (or set `XCLEANER_BROWSER`) | auto-detect |
| `--profile DIR` | Browser profile directory | `./browser_profile` |
| `--attach HOST:PORT` | Attach to an already running browser (advanced) | – |
| `--yes` | Skip the confirmation prompt | off |

### Login

By default the tool uses its own `./browser_profile` folder, separate from your everyday browser. On first run, log in to X manually in the window that opens; the tool waits up to 5 minutes. The session stays in that profile, so you only log in once. **`browser_profile/` contains session cookies: it is git-ignored, never share it.**

Note: since Chrome 136, Chromium-based browsers refuse automation on their *default* profile, so your everyday logged-in session can't be reused; log in once in the tool's own profile. You can also pass another profile folder with `--profile` (all windows using it must be closed), or start a browser yourself with `--remote-debugging-port=9222 --user-data-dir=./browser_profile` and use `--attach 127.0.0.1:9222`.

### Suggested workflow

1. Download your X archive.
2. Run with `--dry-run` and check the number.
3. Run with `--max 20` and verify on your account.
4. Run without a limit (split very large accounts across several days).

### Troubleshooting

| Symptom | Fix |
|---|---|
| "Browser not found" | Pass `--browser` with the executable path |
| Browser opens and closes immediately | Another window is using the same profile; close it or use another `--profile` |
| "Timeline not found" | Not logged in, or wrong username |
| Nothing found | Logged into a different account, or nothing left to delete |
| 5 errors in a row | X's UI probably changed; update the selectors in `cleaner.py` (see `data-testid` values) |

### FAQ

- **Does it steal my password?** No. You log in yourself in your own browser; the code is open and makes no network calls other than through that browser to `x.com`.
- **Can it delete other people's posts?** No.
- **Can I get banned?** No guarantees. Automation may violate X's terms; going slowly lowers the risk but doesn't remove it.
- **Date filters / undoing reposts and likes?** Not supported yet; contributions welcome.

### Tests & license

```bash
pip install -r requirements-dev.txt && pytest
```

MIT licensed, see [LICENSE](LICENSE).

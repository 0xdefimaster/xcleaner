"""Komut satırı arayüzü:  python cli.py kullanici_adi --dry-run"""
import argparse
import os
import sys
import threading

from cleaner import Config, run


def main() -> int:
    p = argparse.ArgumentParser(description="X (Twitter) üzerindeki kendi gönderi ve yanıtlarını sil.")
    p.add_argument("username", help="X kullanıcı adın ya da profil linkin (@ad, ad veya https://x.com/ad)")
    p.add_argument("--browser", default=os.environ.get("XCLEANER_BROWSER", ""),
                   help="Tarayıcı: brave | chrome | edge | chromium ya da .exe yolu (boşsa otomatik aranır; XCLEANER_BROWSER de olur)")
    p.add_argument("--profile", default="browser_profile",
                   help="Tarayıcı profil klasörü (varsayılan: ./browser_profile)")
    p.add_argument("--attach", default="",
                   help="Uzaktan hata ayıklama portu açık bir tarayıcıya bağlan, örn. 127.0.0.1:9222")
    p.add_argument("--dry-run", action="store_true", help="Silmeden yalnızca say")
    p.add_argument("--max", type=int, default=0, dest="max_delete", help="En fazla bu kadar sil (0 = sınırsız)")
    p.add_argument("--delay-min", type=float, default=2.5, help="Silmeler arası en az bekleme (sn)")
    p.add_argument("--delay-max", type=float, default=4.5, help="Silmeler arası en çok bekleme (sn)")
    p.add_argument("--yes", action="store_true", help="Onay sorusunu atla")
    args = p.parse_args()

    cfg = Config(
        username=args.username, browser_path=args.browser, profile_dir=args.profile,
        attach=args.attach, dry_run=args.dry_run, max_delete=args.max_delete,
        min_delay=args.delay_min, max_delay=args.delay_max,
    )
    try:
        cfg.validate()
    except ValueError as exc:
        print(f"Hata: {exc}", file=sys.stderr)
        return 2

    if not cfg.dry_run and not args.yes:
        print(f"@{cfg.username} hesabındaki gönderi ve yanıtlar KALICI olarak silinecek. Bu geri alınamaz.")
        if input("Devam etmek için 'evet' yaz: ").strip().lower() not in {"evet", "yes", "e", "y"}:
            print("İptal edildi.")
            return 1

    stop = threading.Event()
    try:
        run(cfg, lambda msg, status="info": print(f"[{status}] {msg}", flush=True), stop=stop)
    except KeyboardInterrupt:
        stop.set()
        print("\nDurduruldu.")
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())

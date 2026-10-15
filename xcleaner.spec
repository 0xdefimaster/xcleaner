# PyInstaller: pyinstaller xcleaner.spec  ->  dist/XCleaner (.exe Windows'ta)
from PyInstaller.utils.hooks import collect_all, collect_submodules

datas = [("frontend", "frontend")]
binaries = []
hidden = collect_submodules("uvicorn") + ["multipart", "python_multipart"]

# selenium-manager (sürücüyü otomatik indiren yardımcı) paketin içinde durur
sd, sb, sh = collect_all("selenium")
datas += sd; binaries += sb; hidden += sh

a = Analysis(["server.py"], pathex=["."], datas=datas, binaries=binaries,
             hiddenimports=hidden, noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], name="XCleaner",
          console=True, upx=False)

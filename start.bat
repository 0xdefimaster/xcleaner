@echo off
chcp 65001 >nul
cd /d "%~dp0"
title XCleaner

set PY=
py -3 --version >nul 2>nul && set PY=py -3
if not defined PY (
  python --version >nul 2>nul && set PY=python
)
if not defined PY (
  echo.
  echo Python bulunamadi. Simdi indirme sayfasi aciliyor.
  echo Kurulumda "Add python.exe to PATH" kutusunu isaretle, sonra bu dosyayi tekrar calistir.
  start https://www.python.org/downloads/
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo Ilk kurulum yapiliyor, bir kac dakika surebilir...
  %PY% -m venv .venv || goto :hata
)
if not exist ".venv\.deps_ok" (
  ".venv\Scripts\python.exe" -m pip install -q -r requirements.txt || goto :hata
  echo ok> ".venv\.deps_ok"
)

".venv\Scripts\python.exe" server.py
pause
exit /b 0

:hata
echo.
echo Kurulum basarisiz oldu. Internet baglantini kontrol edip tekrar dene.
pause
exit /b 1

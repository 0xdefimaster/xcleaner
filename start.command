#!/usr/bin/env bash
cd "$(dirname "$0")" || exit 1

PY=$(command -v python3 || command -v python)
if [ -z "$PY" ]; then
  echo "Python 3 bulunamadı. https://www.python.org/downloads/ adresinden kur, sonra tekrar çalıştır."
  read -r -p "Kapatmak için Enter..." _
  exit 1
fi

if [ ! -x .venv/bin/python ]; then
  echo "İlk kurulum yapılıyor, birkaç dakika sürebilir..."
  "$PY" -m venv .venv || { echo "Sanal ortam oluşturulamadı."; read -r -p "Enter..." _; exit 1; }
fi
if [ ! -f .venv/.deps_ok ]; then
  .venv/bin/python -m pip install -q -r requirements.txt && touch .venv/.deps_ok \
    || { echo "Kurulum başarısız. İnternet bağlantını kontrol et."; read -r -p "Enter..." _; exit 1; }
fi

.venv/bin/python server.py

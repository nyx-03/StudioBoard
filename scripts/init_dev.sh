#!/usr/bin/env bash
set -e

cd server

python3.14 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

python manage.py migrate
echo "✔ Environnement prêt"
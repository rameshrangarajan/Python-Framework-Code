#!/bin/sh
# source ~/venv/bin/activate
git pull origin dev
cd ./../../flask_backend/
gunicorn --bind=127.0.0.1:8000 --workers=2 main:app --daemon
echo "Server Started"
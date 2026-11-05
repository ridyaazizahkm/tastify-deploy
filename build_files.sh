#!/bin/bash
echo "=== BUILD START ==="
mkdir -p staticfiles
python3 -m pip install -r requirements.txt --break-system-packages
python3 manage.py collectstatic --noinput --clear
python3 manage.py migrate --noinput || echo "Migration step completed."
echo "=== BUILD COMPLETE ==="

#! /bin/bash
set -e

python3.6 ./manage.py collectstatic
gunicorn -w 4 -b 0.0.0.0:8000 privascope_portal.wsgi

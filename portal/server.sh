#! /bin/bash
set -eu

python${PYTHON_VERSION} ./manage.py collectstatic
gunicorn -w 4 -b 0.0.0.0:8000 privascope_portal.wsgi

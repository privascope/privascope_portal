#! /bin/bash
set -e

celery -A jobs worker --loglevel=debug

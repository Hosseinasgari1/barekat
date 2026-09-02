#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install python dependencies
pip install -r requirements.txt

# Collect static files into STATIC_ROOT using WhiteNoise
python manage.py collectstatic --noinput

# Apply database migrations
python manage.py migrate --noinput

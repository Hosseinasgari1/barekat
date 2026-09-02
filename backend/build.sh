#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install python dependencies
pip install -r requirements.txt

# Collect static files into STATIC_ROOT using WhiteNoise
python manage.py collectstatic --noinput

# Apply database migrations
python manage.py migrate --noinput

# Auto-create or update the superadmin account in production
ADMIN_USER="${ADMIN_USERNAME:-superadmin}"
ADMIN_PASS="${ADMIN_PASSWORD:-admin123}"
python manage.py make_admin "$ADMIN_USER" "$ADMIN_PASS" || true

@echo off
"C:\Program Files\PuTTY\plink.exe" -batch -pw pD7y67vu5P root@107.150.20.134 "cd /tmp/barekat_fresh && cp .env.prod .env && docker-compose -f docker-compose.prod.yml up -d --build --force-recreate 2>&1 | tail -n 60"

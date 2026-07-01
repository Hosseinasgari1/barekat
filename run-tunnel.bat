@echo off
cd /d "%~dp0"
powershell -ExecutionPolicy Bypass -File .\run-tunnel.ps1

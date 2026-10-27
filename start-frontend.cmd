@echo off
cd /d "%~dp0frontend"
set DEMO_MODE=true
call npm run dev -- --hostname 127.0.0.1

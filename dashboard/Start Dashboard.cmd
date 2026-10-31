@echo off
cd /d "%~dp0"
echo Smart Dustbin dashboard
echo Open http://localhost:3000 in your browser.
echo Keep this window open while using the dashboard.
call npm.cmd start
pause

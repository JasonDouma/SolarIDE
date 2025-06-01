@echo off
setlocal
set "PID=%1"

taskkill /F /PID %PID%
timeout /t 2 /nobreak >nul
start python SolarIDE.py
exit
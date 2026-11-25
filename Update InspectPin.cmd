@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -File "%~dp0scripts\update_inspectpin.ps1" %*
exit /b %ERRORLEVEL%

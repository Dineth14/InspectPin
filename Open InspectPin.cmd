@echo off
setlocal
"%~dp0.venv\Scripts\python.exe" "%~dp0scripts\open_laptop_app.py" %*
if errorlevel 1 pause

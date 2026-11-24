@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (echo InspectPin Python environment missing. & pause & exit /b 1)
".venv\Scripts\python.exe" scripts\local_demo.py %*
if errorlevel 1 pause

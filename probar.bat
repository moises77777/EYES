@echo off
echo ========================================
echo   EYES - Prueba del Sistema
echo ========================================
cd /d "%~dp0"
.venv\Scripts\python.exe scripts\prueba_sistema.py
pause

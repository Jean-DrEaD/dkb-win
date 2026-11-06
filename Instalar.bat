@echo off
cd /d "%~dp0"
echo Preparando ferramentas (na primeira vez pode levar 10-20 min)...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0preparar-ferramentas.ps1"
if errorlevel 1 (
  echo ERRO ao preparar ferramentas. Veja ferramentas.log
  pause
  exit /b 1
)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0instalador-gui.ps1"

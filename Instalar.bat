@echo off
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0atualizar.ps1"
if errorlevel 2 ( start "DKB" cmd /c "timeout /t 1 >nul & move /y Instalar.bat.new Instalar.bat >nul & Instalar.bat" & exit /b )
echo Preparando ferramentas (na primeira vez pode levar 10-20 min)...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0preparar-ferramentas.ps1"
if errorlevel 1 ( echo ERRO ao preparar ferramentas. Veja ferramentas.log & pause & exit /b 1 )
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0verificar-ambiente.ps1"
if errorlevel 1 ( echo Falha na verificacao / Check failed. Veja verificar-ambiente.log & pause & exit /b 1 )
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0instalador-gui.ps1"
pause

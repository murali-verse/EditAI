@echo off
TITLE EditAI - DaVinci Resolve 21 Chatbot
COLOR 0B
echo ============================================================
echo       EditAI Assistant - DaVinci Resolve 21 Integration
echo ============================================================

REM Set DaVinci Resolve environment variables
set "RESOLVE_SCRIPT_API=C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting"
set "RESOLVE_SCRIPT_LIB=C:\Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.dll"
set "PYTHONPATH=%PYTHONPATH%;%RESOLVE_SCRIPT_API%\Modules\"

REM Run installer to ensure latest scripts are in Resolve's Utility folder
echo [1/2] Verifying DaVinci Resolve script installation...
python "%~dp0davinci_integration\install_davinci_integration.py"

echo.
echo [2/2] Starting EditAI Desktop Chatbot Companion...
python "%~dp0davinci_integration\EditAI_Desktop_Chatbot.py"

pause

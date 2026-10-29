@echo off
TITLE Launch DaVinci Resolve with EditAI Chatbot
COLOR 0A
echo ============================================================
echo   EditAI - Launch DaVinci Resolve with Integrated Chatbot
echo ============================================================
echo.

REM 1. Sync all scripts to DaVinci Resolve directories
echo [1/3] Updating DaVinci Resolve script folders (Lua and Python)...
powershell -Command "$roots = @('C:\ProgramData\Blackmagic Design\DaVinci Resolve\Fusion\Scripts', 'C:\Users\gwm93\AppData\Roaming\Blackmagic Design\DaVinci Resolve\Support\Fusion\Scripts'); $subfolders = @('Edit', 'Deliver', 'Comp', 'Color', 'Utility', 'Tool', ''); $files = @('EditAI_Chatbot.lua', 'EditAI_Chatbot.py', 'davinci_controller.py', 'davinci_nlp_engine.py'); foreach ($r in $roots) { foreach ($sub in $subfolders) { $target = if ($sub -eq '') { $r } else { Join-Path $r $sub }; if (-not (Test-Path $target)) { New-Item -ItemType Directory -Path $target -Force | Out-Null }; foreach ($f in $files) { $src = Join-Path 'D:\Ryathon\davinci_integration' $f; if (Test-Path $src) { Copy-Item $src (Join-Path $target $f) -Force } } } }; Write-Output '[OK] All scripts synchronized.'"

REM 2. Check if DaVinci Resolve is already running
echo.
echo [2/3] Checking DaVinci Resolve process status...
tasklist /FI "IMAGENAME eq Resolve.exe" 2>NUL | find /I /N "Resolve.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo [!] DaVinci Resolve is currently running.
    echo     NOTE: DaVinci Resolve only re-scans the Scripts menu on startup.
    echo.
    echo Press 'R' to Restart Resolve automatically (make sure project is saved!),
    echo or press ANY OTHER KEY to keep your current Resolve session running.
    set /p user_choice="Restart Resolve now? (Y/N): "
    if /I "%user_choice%"=="Y" (
        echo Closing existing DaVinci Resolve instance...
        taskkill /F /IM Resolve.exe
        timeout /t 2 /nobreak >NUL
        echo Starting DaVinci Resolve 21 fresh...
        start "" "C:\Program Files\Blackmagic Design\DaVinci Resolve\Resolve.exe"
    )
) else (
    echo Starting DaVinci Resolve 21...
    start "" "C:\Program Files\Blackmagic Design\DaVinci Resolve\Resolve.exe"
)

REM 3. Launch Desktop Chatbot Companion
echo.
echo [3/3] Starting Desktop Chatbot Companion...
start "" python "D:\Ryathon\davinci_integration\EditAI_Desktop_Chatbot.py"

echo.
echo ============================================================
echo SUCCESS!
echo Inside DaVinci Resolve, go to:
echo   Workspace -> Scripts -> Edit -> EditAI_Chatbot
echo (or Deliver -> EditAI_Chatbot)
echo ============================================================
echo.
pause

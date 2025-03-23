@Echo Off
SETLOCAL EnableDelayedExpansion
for /F "tokens=1,2 delims=#" %%a in ('"prompt #$H#$E# & echo on & for %%b in (1) do     rem"') do (
  set "DEL=%%a"
)
call :colorEcho 6 "Press ENTER to start the setup..."
echo.
pause>nul
cd ..
timeout /t 1 /nobreak>nul
pip install -r requirements.txt

echo Creating file start.bat...
echo python src/main.py > start.bat
echo File start.bat created.

call :colorEcho 4 "Installation completed"

pause>nul
exit
:colorEcho
echo off
<nul set /p ".=%DEL%" > "%~2"
findstr /v /a:%1 /R "^$" "%~2" nul
del "%~2" > nul 2>&1i
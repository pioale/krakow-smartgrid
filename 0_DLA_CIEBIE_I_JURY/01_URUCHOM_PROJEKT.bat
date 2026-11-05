@echo off
title Krakow SmartGrid - Serwer Lokalny
chcp 65001 >nul
cd /d "%~dp0.."

echo ======================================================================
echo   KRAKOW SMARTGRID: Enterprise Web-GIS SCADA Control Center
echo ======================================================================
echo.
echo [1/2] Sprawdzanie srodowiska Python...

set "PYTHON_CMD="
python --version >nul 2>nul
if %errorlevel% equ 0 (
    set "PYTHON_CMD=python"
) else (
    py --version >nul 2>nul
    if %errorlevel% equ 0 (
        set "PYTHON_CMD=py"
    ) else (
        if exist "C:\Python314\python.exe" (
            set "PYTHON_CMD=C:\Python314\python.exe"
        )
    )
)

if "%PYTHON_CMD%"=="" (
    echo [BLAD] Nie znaleziono interpretera Python w systemie!
    echo Upewnij sie, ze Python jest zainstalowany i dodany do PATH.
    pause
    exit /b 1
)

echo [2/2] Uruchamianie serwera i konsoli SCADA...
echo.
echo ----------------------------------------------------------------------
echo   SERWER DZIALA. Przegladarka otworzy sie automatycznie.
echo   Adres lokalny: http://localhost:8080/krakow_smartgrid_scada.html
echo   Aby zakonczyc prace serwera, zamknij to okno.
echo ----------------------------------------------------------------------
echo.

%PYTHON_CMD% server.py --page krakow_smartgrid_scada.html

pause

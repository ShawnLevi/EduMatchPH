@echo off
setlocal
title EduMatch PH Launcher
cd /d "%~dp0"

REM ===== EDIT THESE ONLY IF SOMETHING IS NOT FOUND =====
set "BACKEND=%~dp0edumatch_backend_v2"
set "FRONTEND=%~dp0EduMatchPH_Frontend"
set "XAMPP=C:\xampp"
REM =====================================================

REM ---- Look one folder deeper if the app is nested ----
if not exist "%BACKEND%\app.py" if exist "%BACKEND%\edumatch_backend_v2\app.py" set "BACKEND=%BACKEND%\edumatch_backend_v2"
if not exist "%FRONTEND%\index.html" if exist "%FRONTEND%\EduMatchPH_Frontend\index.html" set "FRONTEND=%FRONTEND%\EduMatchPH_Frontend"

REM ---- Find the SQL file: prefer a schema file in the database folder ----
set "SQLFILE="
for %%f in ("%~dp0database\*schema*.sql") do set "SQLFILE=%%f"
if not defined SQLFILE for %%f in ("%~dp0database\*.sql") do set "SQLFILE=%%f"
if not defined SQLFILE for %%f in ("%~dp0*.sql") do set "SQLFILE=%%f"

echo ===== EduMatch PH =====
echo Backend : %BACKEND%
echo Frontend: %FRONTEND%
echo SQL file: %SQLFILE%
echo.

REM ---- 1. Find Python ----
set "PY=python"
python --version >nul 2>&1
if errorlevel 1 (
  set "PY=py"
  py --version >nul 2>&1
  if errorlevel 1 (
    echo [ERROR] Python was not found.
    echo Install Python 3.11 or newer and tick "Add Python to PATH".
    pause
    exit /b 1
  )
)

REM ---- 2. Check that the files exist ----
if not exist "%BACKEND%\app.py" (
  echo [ERROR] Cannot find app.py in: %BACKEND%
  echo Edit the BACKEND line at the top of this file.
  pause
  exit /b 1
)
if not exist "%FRONTEND%\index.html" (
  echo [ERROR] Cannot find index.html in: %FRONTEND%
  echo Edit the FRONTEND line at the top of this file.
  pause
  exit /b 1
)
if not exist "%XAMPP%\mysql\bin\mysqld.exe" (
  echo [ERROR] XAMPP not found at: %XAMPP%
  echo Install XAMPP or edit the XAMPP line at the top of this file.
  pause
  exit /b 1
)

REM ---- 3. Start MySQL if it is not running ----
tasklist /fi "imagename eq mysqld.exe" | find /i "mysqld.exe" >nul
if errorlevel 1 (
  echo Starting MySQL...
  start "MySQL" /min "%XAMPP%\mysql\bin\mysqld.exe" --defaults-file="%XAMPP%\mysql\bin\my.ini" --standalone
  timeout /t 8 /nobreak >nul
)

REM ---- 4. Create and import the database if it is empty ----
pushd "%XAMPP%\mysql\bin"
mysql.exe -u root -e "CREATE DATABASE IF NOT EXISTS edumatch_db"
set "TBL=0"
for /f "usebackq" %%i in (`mysql.exe -u root -N -e "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='edumatch_db'"`) do set "TBL=%%i"
if "%TBL%"=="0" (
  if not defined SQLFILE (
    popd
    echo [ERROR] No .sql file found. Put it in the database folder.
    pause
    exit /b 1
  )
  echo Importing database - first time only...
  mysql.exe -u root edumatch_db < "%SQLFILE%"
)
popd

REM ---- 5. First-time Python setup ----
if not exist "%BACKEND%\venv\Scripts\python.exe" (
  echo First-time setup: installing packages. This can take a few minutes...
  pushd "%BACKEND%"
  %PY% -m venv venv
  venv\Scripts\python.exe -m pip install -r requirements.txt
  if errorlevel 1 (
    echo [ERROR] Package install failed.
    rmdir /s /q venv
    popd
    pause
    exit /b 1
  )
  popd
)

REM ---- 6. Start backend and frontend in their own windows ----
echo Starting backend...
start "EduMatch Backend" /D "%BACKEND%" cmd /k venv\Scripts\python.exe app.py
echo Starting frontend...
start "EduMatch Frontend" /D "%FRONTEND%" cmd /k %PY% -m http.server 5500

timeout /t 5 /nobreak >nul
start "" http://localhost:5500/index.html

echo.
echo EduMatch PH is running. To stop it, close the Backend and Frontend windows.
echo.
pause

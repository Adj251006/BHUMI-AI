@echo off
REM ==============================================================================
REM  BHUMI-AI: 1-Click Startup Script for Windows
REM  SIH26016 — Ministry of Rural Development
REM ==============================================================================

echo ==============================================================================
echo            BHUMI-AI: National Land Acquisition & Management System           
echo                      1-Click Windows Local Launcher                          
echo ==============================================================================
echo.

set ROOT_DIR=%~dp0
set BACKEND_DIR=%ROOT_DIR%backend
set FRONTEND_DIR=%ROOT_DIR%frontend

REM 1. Check Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in your PATH.
    echo Please install Python 3.10+ from https://www.python.org
    pause
    exit /b 1
)

REM 2. Check Node & NPM
where npm >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Node.js and npm are required.
    echo Please install Node.js 18+ from https://nodejs.org
    pause
    exit /b 1
)

REM 3. Setup backend .env
if not exist "%BACKEND_DIR%\.env" (
    echo [*] Creating backend\.env from .env.example...
    copy "%BACKEND_DIR%\.env.example" "%BACKEND_DIR%\.env" >nul
)

REM 4. Setup Python Virtual Environment
echo.
echo [*] Checking Backend Virtual Environment...
if not exist "%BACKEND_DIR%\venv" (
    echo [*] Creating Python virtualenv in backend\venv...
    python -m venv "%BACKEND_DIR%\venv"
)

call "%BACKEND_DIR%\venv\Scripts\activate.bat"
python -c "import fastapi, uvicorn, sqlalchemy" >nul 2>nul
if %errorlevel% neq 0 (
    echo [*] Installing backend dependencies...
    python -m pip install --upgrade pip
    pip install -r "%BACKEND_DIR%\requirements.txt"
) else (
    echo [OK] Backend dependencies verified.
)

REM 5. Setup Frontend Dependencies
echo.
echo [*] Checking Frontend Dependencies...
if not exist "%FRONTEND_DIR%\node_modules" (
    echo [*] Installing frontend npm packages...
    cd /d "%FRONTEND_DIR%"
    call npm install
    cd /d "%ROOT_DIR%"
) else (
    echo [OK] Frontend packages verified.
)

REM 6. Launch Services
echo.
echo ==============================================================================
echo   Launching Backend and Frontend Servers...
echo   Backend:  http://127.0.0.1:8000
echo   Frontend: http://localhost:5173
echo ==============================================================================
echo.

start "BHUMI-AI Backend" cmd /k "cd /d %BACKEND_DIR% && call venv\Scripts\activate.bat && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000"
timeout /t 3 >nul
start "BHUMI-AI Frontend" cmd /k "cd /d %FRONTEND_DIR% && npm run dev"
timeout /t 3 >nul

start http://localhost:5173
echo.
echo [DONE] Both servers launched in background windows.
echo To stop, simply close the opened Command Prompt windows.
pause

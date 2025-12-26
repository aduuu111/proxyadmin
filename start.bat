@echo off
echo ========================================
echo ProxyAdminPanel Startup Script
echo ========================================
echo.

REM Check if .env exists
if not exist .env (
    echo [ERROR] .env file not found!
    echo Please copy .env.example to .env and configure it.
    pause
    exit /b 1
)

REM Check if database exists
if not exist proxy_admin.db (
    echo [INFO] Database not found. Initializing...
    python init_db.py
    if errorlevel 1 (
        echo [ERROR] Database initialization failed!
        pause
        exit /b 1
    )
    echo [SUCCESS] Database initialized!
    echo.
)

echo [INFO] Starting FastAPI backend...
echo Backend will be available at: http://localhost:8000
echo API Documentation: http://localhost:8000/docs
echo.

start cmd /k "title ProxyAdminPanel Backend && python main.py"

timeout /t 3 /nobreak >nul

echo.
echo [INFO] To start the frontend:
echo   1. Open a new terminal
echo   2. cd frontend
echo   3. npm install (first time only)
echo   4. npm run dev
echo.
echo Frontend will be available at: http://localhost:3000
echo.
echo ========================================
echo Press any key to exit...
pause >nul

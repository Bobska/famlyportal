@echo off
echo ========================================
echo FamlyPortal - Standard Development Server
echo (WebSocket features will not work)
echo ========================================
echo.
echo Activating virtual environment...
call .venv\Scripts\activate.bat

echo.
echo Starting Django development server...
echo Server will be available at: http://127.0.0.1:8000
echo.
echo Press Ctrl+C to stop the server
echo.

python manage.py runserver

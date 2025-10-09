@echo off
echo ========================================
echo FamlyPortal Development Server
echo ========================================
echo.
echo Activating virtual environment...
call .venv\Scripts\activate.bat

echo.
echo Collecting static files...
python manage.py collectstatic --noinput

echo.
echo Starting server with WebSocket support...
echo Server will be available at: http://127.0.0.1:8000
echo.
echo Press Ctrl+C to stop the server
echo.

python -m daphne -b 127.0.0.1 -p 8000 famlyportal.asgi:application

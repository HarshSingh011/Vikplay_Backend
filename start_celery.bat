@echo off
echo ========================================
echo Starting Celery Worker with Beat
echo ========================================
echo.

cd /d "%~dp0"

echo Activating virtual environment...
call .venv\Scripts\activate.bat

echo.
echo Starting Celery...
echo - Worker: Processing async tasks
echo - Beat: Running periodic tasks (cleanup every hour)
echo.
echo Press Ctrl+C to stop
echo.

celery -A celery_config worker --beat --loglevel=info --pool=solo

pause

@echo off
echo ========================================
echo Starting Redis Server for FamlyPortal
echo ========================================
echo.

REM Check if Redis is installed in common locations
if exist "C:\Program Files\Redis\redis-server.exe" (
    echo Found Redis at: C:\Program Files\Redis\
    cd "C:\Program Files\Redis"
    redis-server.exe
    goto :end
)

if exist "C:\Redis\redis-server.exe" (
    echo Found Redis at: C:\Redis\
    cd C:\Redis
    redis-server.exe
    goto :end
)

if exist "%USERPROFILE%\Redis\redis-server.exe" (
    echo Found Redis at: %USERPROFILE%\Redis\
    cd "%USERPROFILE%\Redis"
    redis-server.exe
    goto :end
)

echo.
echo ERROR: Redis not found!
echo.
echo Please install Redis from:
echo https://github.com/microsoftarchive/redis/releases
echo.
echo Or download from:
echo https://github.com/tporadowski/redis/releases
echo.
echo Extract to one of these locations:
echo - C:\Program Files\Redis\
echo - C:\Redis\
echo - %USERPROFILE%\Redis\
echo.
pause

:end

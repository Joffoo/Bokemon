@echo off
cd /d "%~dp0"
echo Starting Bokeman local server... close this window to stop.
where python >nul 2>nul && (python server.py --open & goto :eof)
where py >nul 2>nul && (py server.py --open & goto :eof)
echo Python not found. Please install Python 3 from https://www.python.org/ and try again.
pause

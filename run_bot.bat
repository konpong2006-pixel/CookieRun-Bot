@echo off
echo ==============================================
echo Cookie Run Auto Farm Bot (Web UI Mode)
echo ==============================================
echo Checking required Python libraries...
pip install -r requirements.txt
echo.
echo Starting Web Server...
python server.py
pause

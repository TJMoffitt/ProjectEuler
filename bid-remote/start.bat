@echo off
rem Double-click to start Bid Remote on Windows (run setup steps in README.md first).
cd /d "%~dp0"
call .venv\Scripts\activate.bat
python app.py
pause

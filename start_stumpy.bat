@echo off
title Stumpy AI - The Adaptive AI Companion
cd /d "%~dp0"
echo ============================================================
echo   Starting Stumpy AI...
echo   Open your browser at: http://localhost:8000
echo ============================================================
python -u backend/run.py
pause

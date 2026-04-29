@echo off
echo Starting Faheem's LinkedIn AI Server...
echo Open your browser to http://127.0.0.1:8000
python -X utf8 -m uvicorn app:app --reload
pause

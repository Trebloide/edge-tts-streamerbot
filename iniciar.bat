@echo off
cd /d "%~dp0"
py -3 -c "import edge_tts, pygame" 2>nul || py -3 -m pip install -r requirements.txt
start "" pyw -3 stream_tts.py

@echo off
rem Genera dist\StreamTTS.exe (un solo archivo, sin necesidad de Python para usarlo).
cd /d "%~dp0"
py -3 -m pip install -r requirements.txt pyinstaller || exit /b 1
py -3 -m PyInstaller --noconfirm --onefile --windowed --name StreamTTS --icon icon.ico ^
  --add-data "icon.ico;." --add-data "overlay.html;." ^
  --hidden-import pygame._sdl2.audio --hidden-import pystray._win32 ^
  stream_tts.py

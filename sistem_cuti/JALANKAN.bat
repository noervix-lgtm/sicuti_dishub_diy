@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Sistem Cuti
where python >nul 2>nul
if errorlevel 1 (
  echo Python belum terpasang atau belum masuk PATH.
  echo Pasang dari https://www.python.org/downloads/ dan CENTANG "Add python.exe to PATH".
  pause & exit /b 1
)
if not exist venv (
  echo Menyiapkan pertama kali, mohon tunggu...
  python -m venv venv || (echo Gagal membuat venv & pause & exit /b 1)
  venv\Scripts\python -m pip install -r requirements.txt || (echo Gagal memasang library. Cek koneksi internet. & pause & exit /b 1)
)
venv\Scripts\python app.py
pause

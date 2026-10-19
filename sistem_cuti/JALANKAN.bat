@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Sistem Cuti
if exist venv\Scripts\python.exe (
  goto run
)
where python >nul 2>nul
if errorlevel 1 (
  if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
    set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
  ) else (
    echo Python belum terpasang atau belum masuk PATH.
    echo Pasang dari https://www.python.org/downloads/ dan CENTANG "Add python.exe to PATH".
    pause & exit /b 1
  )
) else (
  set "PYTHON_EXE=python"
)
if not exist venv (
  echo Menyiapkan pertama kali, mohon tunggu...
  "%PYTHON_EXE%" -m venv venv || (echo Gagal membuat venv & pause & exit /b 1)
  venv\Scripts\python -m pip install -r requirements.txt || (echo Gagal memasang library. Cek koneksi internet. & pause & exit /b 1)
)
:run
venv\Scripts\python.exe app.py
pause

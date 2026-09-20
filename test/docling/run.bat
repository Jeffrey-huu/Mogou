@echo off
setlocal

rem Run from this file's location so the launcher works from any current directory.
cd /d "%~dp0\..\.."
set "UV_CACHE_DIR=%CD%\.uv-cache"

uv run --project submodules\docling --extra standard --extra format-audio python test\docling\test_docling_batch.py
set "exit_code=%ERRORLEVEL%"
endlocal & exit /b %exit_code%

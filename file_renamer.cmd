@echo off
REM Wrapper to run the Python script from anywhere
setlocal
set "SCRIPT_DIR=%~dp0"

REM Prefer project venv if available
if exist "%SCRIPT_DIR%venv\Scripts\python.exe" (
  "%SCRIPT_DIR%venv\Scripts\python.exe" "%SCRIPT_DIR%file_renamer.py" %*
  goto :eof
)

REM Prefer Windows Python launcher if available, else python
where py >nul 2>&1
if %ERRORLEVEL%==0 (
  py "%SCRIPT_DIR%file_renamer.py" %*
) else (
  python "%SCRIPT_DIR%file_renamer.py" %*
)

endlocal

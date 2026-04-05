@echo off
setlocal

cd /d "%~dp0.."
".venv\Scripts\python.exe" "src\collect_openphish_snapshots.py" --include-openphish --run-once

endlocal

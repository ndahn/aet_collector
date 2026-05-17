@echo off
CALL "%userprofile%\miniforge3\Scripts\activate.bat"
CALL conda activate aet_collector
pip install pyinstaller

REM "=== PYINSTALLER ==="
IF EXIST dist RMDIR /S /Q dist
pyinstaller aet_collector.py --onefile  REM --icon=yonder.ico

REM "=== COPY ADDITIONAL FILES ==="
REM COPY LICENSE dist\
REM COPY README.md dist\
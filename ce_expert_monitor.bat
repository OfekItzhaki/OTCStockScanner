@echo off
REM Change directory to the folder where the batch file is located
cd /d "%~dp0"

REM Run the Python script located in the same folder as the .bat file
python "ce_expert_monitor.py"

REM Pause to see output/errors if run manually (optional)
pause

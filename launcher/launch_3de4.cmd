@echo off

set NUKE_PATH=C:\Program Files\Nuke14.0v7
set EQUALIZER_PATH=C:\Program Files\3DE4_win64_r7.1v2\bin\3DE4.exe

set PYTHON_CUSTOM_SCRIPTS_3DE4=%~dp0..\scripts\equalizer
for %%i in ("%PYTHON_CUSTOM_SCRIPTS_3DE4%") do set PYTHON_CUSTOM_SCRIPTS_3DE4=%%~fi

echo NUKE_PATH=%NUKE_PATH%
echo EQUALIZER_PATH=%EQUALIZER_PATH%
echo PYTHON_CUSTOM_SCRIPTS_3DE4=%PYTHON_CUSTOM_SCRIPTS_3DE4%

"%EQUALIZER_PATH%

pause

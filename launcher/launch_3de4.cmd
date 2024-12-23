@echo off


rem userconfig
set EQUALIZER_EXECUTABLE_PATH=C:\Program Files\3DE4_win64_r7.1v2\bin\3DE4.exe
set NUKE_EXECUTABLE_PATH=C:\Program Files\Nuke14.0v7\Nuke14.0.exe
rem userconfig


set SCRIPTS_EQUALIZER_PATH=%~dp0..\MatchMoveExporter\scripts\tde
for %%i in ("%SCRIPTS_EQUALIZER_PATH%") do set SCRIPTS_EQUALIZER_PATH=%%~fi

set MATCH_MOVE_EXPORTER_PATH=%~dp0..
for %%i in ("%MATCH_MOVE_EXPORTER_PATH%") do set MATCH_MOVE_EXPORTER_PATH=%%~fi

set PYTHON_CUSTOM_SCRIPTS_3DE4=%SCRIPTS_EQUALIZER_PATH%;%MATCH_MOVE_EXPORTER_PATH%

set MMEXPORTER_EXPORT_FOLDER_IS_VERSION=1

echo EQUALIZER_EXECUTABLE_PATH=%EQUALIZER_EXECUTABLE_PATH%
echo NUKE_EXECUTABLE_PATH=%NUKE_EXECUTABLE_PATH%
echo PYTHON_CUSTOM_SCRIPTS_3DE4=%PYTHON_CUSTOM_SCRIPTS_3DE4%

"%EQUALIZER_EXECUTABLE_PATH%

pause

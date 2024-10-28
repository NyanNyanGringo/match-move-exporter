# import os
# import subprocess
#
# # userconfig
# EQUALIZER_EXECUTABLE_PATH = r"C:\Program Files\3DE4_win64_r7.1v2\bin\3DE4.exe"
# NUKE_EXECUTABLE_PATH = r"C:\Program Files\Nuke14.0v7\Nuke14.0.exe"
# # userconfig
#
# # Get the current script directory
# current_dir = os.path.dirname(os.path.abspath(__file__))
#
# # Set paths
# SCRIPTS_EQUALIZER_PATH = os.path.abspath(os.path.join(current_dir, '..', 'scripts', 'equalizer'))
# MATCH_MOVE_EXPORTER_PATH = os.path.abspath(os.path.join(current_dir, '..'))
#
# # Define custom Python scripts path for Equalizer
# PYTHON_CUSTOM_SCRIPTS_3DE4 = f"{SCRIPTS_EQUALIZER_PATH};{MATCH_MOVE_EXPORTER_PATH}"
#
# # Set environment variables
# os.environ['NUKE_EXECUTABLE_PATH'] = NUKE_EXECUTABLE_PATH
# os.environ['PYTHON_CUSTOM_SCRIPTS_3DE4'] = PYTHON_CUSTOM_SCRIPTS_3DE4
#
# # Output the paths (to verify they are set)
# print(f"NUKE_EXECUTABLE_PATH={os.environ['NUKE_EXECUTABLE_PATH']}")
# print(f"PYTHON_CUSTOM_SCRIPTS_3DE4={os.environ['PYTHON_CUSTOM_SCRIPTS_3DE4']}")
#
# # Run Equalizer executable
# subprocess.run([EQUALIZER_EXECUTABLE_PATH])
#
# # Pause equivalent in Python
# input("Press Enter to continue...")

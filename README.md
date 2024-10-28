# MatchMoveExporter


###### Requires: 3DEqualizer 7.1+, Nuke 14.0+


#### [Watch YouTube guide (in progress)](https://i.pinimg.com/originals/09/2c/72/092c72db80eae3f31b8420ed8e60bc73.jpg)


Export **all** 3D tracking data from 3DEqualizer in **one click**:
- Geo
- STmap
- Undistort
- Alembic and FBX
- Dailies (.mov)
- Nuke project


### Windows installation for artists:

1. Download the repository to any folder.
2. In `launcher/launch_3de4.cmd` file fill:
- EQUALIZER_EXECUTABLE_PATH (path to 3DE4.exe)
- NUKE_EXECUTABLE_PATH (path to Nuke.exe)
3. Launch `launcher/launch_3de4.cmd` and run `MMExporter/MatchMove Exporter` action.


### MacOS installation for artists:
in progress...


### Linux installation for artists:
in progress...


### Pipeline integration:
Place `match-move-exporter` folder (contains `MatchMoveExporter`) somewhere.

Here is necessary environment variables to run 3DEqualizer4:
```python
import os
import subprocess

# Path to Nuke executable.
os.environ["NUKE_EXECUTABLE_PATH"] = "/path/to/Nuke.exe"

# Path to 3DEqualizer Scripts and Root (so 3DEqualizer has access to MatchMoveExporter.lib).
root_path = "/path/to/match-move-exporter"
scripts_path = "/path/to/MatchMoveExporter/scripts/tde"
os.environ["PYTHON_CUSTOM_SCRIPTS_3DE4"] = root_path + os.path.pathsep + scripts_path

# Run 3DEqualizer.
subprocess.run(["/path/to/3DE4.exe"])
```
Optioanl environment variables. Leave blank or don't add to code to ignore them:
```python
# By default name is "sh000_00_track_v001".
os.environ["MMEXPORTER_CUSTOM_DEFAULT_NAME"] = ""

# By default pattern is "[seq_name]_sh<shot_number>_<task_number>_track_v000_[definition]".
os.environ["MMEXPORTER_CUSTOM_NAME_PATTERN"] = ""

# Path to custom log path. Default is "/match-move-exporter/logs/log.log".
os.environ["MMEXPORTER_CUSTOM_LOG_PATH"] = ""

# Assign value "1", if lens distortion plugins already installed to Nuke.
# Otherwise, path will be "/plugins/3de4_lens_distortion_plugin_kit"
os.environ["MMEXPORTER_NUKE_LENS_PLUGINS_INSTALLED"] = ""

# Assign value "1", to name export folder as version + postfix.
# Otherwise, it will has full name.
os.environ["MMEXPORTER_EXPORT_FOLDER_IS_VERSION"] = ""
```
Also:
- You can delete `launcher` folder.
- You can delete `plugins` folder if you use `MMEXPORTER_NUKE_LENS_PLUGINS_INSTALLED` and lens already installed to Nuke.


### 3DEqualizer knowledge base:

- [Python scripting interface 3DE4 R7.1](https://www.3dequalizer.com/user_daten/sections/tech_docs/txt/py_doc_r7.1.txt)
- [Python Vector Library](https://www.3dequalizer.com/user_daten/sections/tech_docs/vl/html/vl.xhtml)
- [Python Command "setWidgetShortcut()" Opcodes](https://www.3dequalizer.com/?site=tech_docs&id=121122_01)
- [Environment variables in 3DE4](https://www.3dequalizer.com/?site=tech_docs&id=121221_01)

# MatchMoveExporter

[![](https://img.shields.io/badge/return-home_-blue.svg)](https://github.com/NyanNyanGringo/match-move-exporter)

###### Requirements: Windows, 3DEqualizer 7.1+, Nuke 14.0+

Created by [DobroCCS](https://dobrocreative.com/en)  
Author: [Vladislav Parfentev](https://t.me/VladislavParfentev).
Special thanks to: [Yury Bodolanov](https://t.me/bodolanov)

---

### Export tracking data from 3DEqualizer with one button

![3DE4_rXrdtNS6ux.png](resources%2F3DE4_rXrdtNS6ux.png)

File structure after export. A folder with all files is created next to the 3DEqualizer script.
```javascript
├── geo
│   └── geometry.obj
├── stmap | 
│   └── sh000_00_track_v001.####.exr | "Exr Zip Raw"
├── undistort
│   └── sh000_00_track_v001.####.exr | "Exr Dwaa Raw"
├── sh000_00_track_v001.3de
├── sh000_00_track_v001.abc | "Camera + Geo"
├── sh000_00_track_v001.fbx | "Camera + Geo"
├── sh000_00_track_v001.mov | "Mov H264 Srgb"
└── sh000_00_track_v001.nk
```

---

### Windows installation for artists:

1. Download the repository to any folder.
![browser_MDE9dB50sq.png](resources%2Fbrowser_MDE9dB50sq.png)
2. In the `launcher/launch_3de4.cmd` file, change the path to `3DE4.exe` and `Nuke.exe`:
![Notepad_LXr38f0deO.png](resources%2FNotepad_LXr38f0deO.png)
3. Run `launcher/launch_3de4.cmd`. You will see the `MMExporter` menu at the bottom of the program:
![3DE4_bVBTTrs462.png](resources%2F3DE4_bVBTTrs462.png)

---

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
You can delete `launcher` and `resources` folders.

You can delete `plugins` folder if you use `MMEXPORTER_NUKE_LENS_PLUGINS_INSTALLED` and [lenses](https://www.3dequalizer.com/?site=tech_docs&id=110216_01) already installed to Nuke.

---

### 3DEqualizer knowledge base:

- [Python scripting interface 3DE4 R7.1](https://www.3dequalizer.com/user_daten/sections/tech_docs/txt/py_doc_r7.1.txt)
- [Python Vector Library](https://www.3dequalizer.com/user_daten/sections/tech_docs/vl/html/vl.xhtml)
- [Python Command "setWidgetShortcut()" Opcodes](https://www.3dequalizer.com/?site=tech_docs&id=121122_01)
- [Environment variables in 3DE4](https://www.3dequalizer.com/?site=tech_docs&id=121221_01)

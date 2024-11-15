# MatchMoveExporter

[![en](https://img.shields.io/badge/lang-english_-blue.svg)](https://github.com/NyanNyanGringo/match-move-exporter/blob/main/README.en.md)

###### Требования: Windows, 3DEqualizer 7.1+, Nuke 14.0+

Создано студией [DobroCCS](https://dobrocreative.com/en)  
Автор: [Владислав Парфентьев](https://t.me/VladislavParfentev).
Особая благодарность: [Юрий Бодоланов](https://t.me/bodolanov)

---

# TODO: написать что не поддерживается Frame Range

### Экспорт трекинг-даты из 3DEqualizer по одной кнопке

![3DE4_rXrdtNS6ux.png](resources%2F3DE4_rXrdtNS6ux.png)

Структура файлов после экспорта. Папка со всеми файлами создается рядом со скриптом 3DEqualizer.
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

Опционально (можно включить в userconfig.py):
├── undistort_downscale
│   └── sh000_00_track_v001.####.exr | "Exr Dwaa Raw"
├── Раздельный экспорт Camera и Geo для .abc и .fbx
├── sh000_00_track_undistort_v001.nk | Только Undistort нода
└── sh000_00_track_v001.mel
```

---

### Установка для исполнителей (Windows)

1. Скачайте репозиторий и разархивируйте в любое удобное место:
![browser_MDE9dB50sq.png](resources%2Fbrowser_MDE9dB50sq.png)
2. В файле `launcher/launch_3de4.cmd`, измените путь до `3DE4.exe` и `Nuke.exe`:
![Notepad_LXr38f0deO.png](resources%2FNotepad_LXr38f0deO.png)
3. Запустите `launcher/launch_3de4.cmd`. У вас появится меню `MMExporter` внизу программы.
![3DE4_bVBTTrs462.png](resources%2F3DE4_bVBTTrs462.png)

---

### Интеграция в студийный пайплайн:
Поместите папку `match-move-exporter` (содержит `MatchMoveExporter`) в любое место.

Ниже представлены необходимые переменные окружения:
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
Для настройки программы под студию используйте файл `userconfig.py`

Вы можете удалить папки `launcher` и `resources`. 

Вы можете удалить папку `plugins`, если [линзы](https://www.3dequalizer.com/?site=tech_docs&id=110216_01) уже
установлены в Nuke или вы изменили к ним путь в методе get_3de4_lenses_for_nuke_path()

---

### 3DEqualizer база знаний:

- [Python scripting interface 3DE4 R7.1](https://www.3dequalizer.com/user_daten/sections/tech_docs/txt/py_doc_r7.1.txt)
- [Python Vector Library](https://www.3dequalizer.com/user_daten/sections/tech_docs/vl/html/vl.xhtml)
- [Python Command "setWidgetShortcut()" Opcodes](https://www.3dequalizer.com/?site=tech_docs&id=121122_01)
- [Environment variables in 3DE4](https://www.3dequalizer.com/?site=tech_docs&id=121221_01)

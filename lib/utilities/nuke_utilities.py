import os
import tempfile


# private


def _create_script_file(script: str) -> str:
    dir_path = os.path.join(tempfile.gettempdir(), "match_move_exporter")

    os.makedirs(dir_path, exist_ok=True)

    filepath = os.path.join(dir_path, "NUKE_PYTHON_SCRIPT.py")

    with open(filepath, "w") as file:
        file.write(script)

    return filepath


# public


def get_export_py_script(return_file: bool = True) -> str:
    """
    Скрипт для Nuke, который экспортирует трекинг-дату:
    - Дэйлиз .mov
    - STMap дисторсию .exr
    - Камеру и геометрию в формате .abc и .fbx
    - Undistort в формате .exr
    - Папку geo, где будет вся геометрия

    На входе скрипту требуются аргументы:
    - argv[1]: Подготовленный под экспорт скрипт .nk

    Важно: для корректной работы скрипта необходим подготовленный '.nk' файл, который
    создается на этапе экспорта из 3DEqualizer или SynthEyes. Также, должен быть
    доступ к импорту файлов из папки lib.
    """
    script = """
import sys

import nuke

from lib.utilities.log_utilities import setup_or_get_logger


LOGGER = setup_or_get_logger(force_setup=True, use_console_handler=True)
LOGGER.info("Nuke works good!")
NUKE_SCRIPT = sys.argv[1]


nuke.scriptOpen(NUKE_SCRIPT)


node = nuke.createNode("Blur")
LOGGER.info(f"Blur node created: {node.name()}")


nuke.scriptSave(NUKE_SCRIPT)

"""
    if return_file:
        return _create_script_file(script)
    return script

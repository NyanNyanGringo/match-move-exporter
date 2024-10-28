import os
import re
import platform
import subprocess


def get_root_path() -> str:
    """Return match-move-exporter path."""
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def get_match_move_exporter_path() -> str:
    """Return MatchMoveExporter path."""
    return os.path.join(get_root_path(), "MatchMoveExporter")


def get_3de4_lenses_for_nuke_path() -> str:
    return os.path.join(get_root_path(), "plugins", "3de4_lens_distortion_plugin_kit")


def get_version_with_postfix(name: str) -> str:
    """Using regular expression detect version and postfix in name.
    If not found return empty string."""
    versions = re.findall("_v\d+(?:_.+)?", name)
    if versions:
        return versions[-1][1:]  # return last version and delete first symbol "_"
    return ""


def open_in_explorer(path: str) -> None:
    """Open file or dir path in explorer, and select it."""
    operatingSystem = platform.system()

    if os.path.exists(path):

        if operatingSystem == "Windows":
            subprocess.call(("explorer", "/select,", path))
        elif operatingSystem == "Darwin":
            subprocess.call(["open", "-R", path])
        else:
            subprocess.call(["nautilus", "--select", path])

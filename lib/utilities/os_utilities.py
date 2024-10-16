import os
import re


def get_root_path() -> str:
    """return MatchMoveExporter path"""
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def get_version_with_postfix(name: str) -> str:
    versions = re.findall("_v\d+(?:_.+)?", name)
    if versions:
        return versions[-1]
    return ""

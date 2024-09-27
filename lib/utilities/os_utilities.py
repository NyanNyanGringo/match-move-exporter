import os


def get_root_path() -> str:
    """return MatchMoveExporter path"""
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

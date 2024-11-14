"""
In this file you can setup MatchMoveExporter for self- or studio- pipeline.

# TODO: copy nuke undistort path = use with intermediate name
# TODO: Use dailies Gizmo
# TODO: User Frame Range in Read node.
"""

import os
from typing import Tuple, Dict

from MatchMoveExporter.lib.utilities.os_utilities import get_root_path, get_version_with_postfix
from MatchMoveExporter.lib.utilities.userconfig_utilities import CameraConfig


class UserConfig:
    # Choose which files to export
    export_geo: bool = True
    export_stmap: bool = True
    export_undistort: bool = True
    export_undistort_downscale: bool = True
    export_tde4_project: bool = True
    export_abc: bool = True
    export_fbx: bool = True
    export_dailies: bool = True
    export_nk_project: bool = True
    export_undistortn_nk_project: bool = False
    export_maya: bool = False

    # Other
    separate_cam_and_geo: bool = False

    @staticmethod
    def get_default_name() -> str:
        """
        You can write your custom logic for getting Default Name.
        By default, it returns constant string.
        For example, you can get this name from 3DE4 script name.
        """
        return "sh000_00_track_v001"

    @staticmethod
    def get_name_pattern() -> str:
        """
        You can write your custom logic for getting Name Pattern.
        By default, it returns constant string.
        """
        return "[seq_name]_sh<shot_number>_<task_number>_track_v000_[definition]"

    @staticmethod
    def get_log_file_path() -> str:
        """
        You can write your custom logic for getting Log Path.
        By default, it returns '.../match-move-exporter/logs/log.log'
        """
        path = os.path.join(
            get_root_path(),
            "logs",
            "logs.log"
        )

        os.makedirs(os.path.dirname(path), exist_ok=True)

        return path

    @staticmethod
    def get_geo_folder_name() -> str:
        return "geo"

    @staticmethod
    def get_3de4_lenses_for_nuke_path() -> str:
        """Return path to 3DE4 Lens Distortion plugin for Nuke.
        You can write your custom logic.
        Note: if you don't want to add any 3DE4 plugins for Nuke, just
        return empty string."""
        return os.path.join(get_root_path(), "plugins", "3de4_lens_distortion_plugin_kit")

    @staticmethod
    def get_export_folder_name(name: str) -> str:
        """
        You can write your custom logic for getting Export Folder.

        Note: just return name if you don't want to rename Export Folder.

        :param name: name entered by user.
        :return: export folder name as version with postfix. If version
        not detected - return name itself.
        """
        return get_version_with_postfix(name)

    @staticmethod
    def get_undistort_configuration() -> dict:
        """
        You can write your custom logic for getting Undistort Write Node values.
        Method should return dict where key is knob name of Write Node. Usually
        used to set colorspace/raw, file_type and compression options.
        """
        knob_values = {
            "raw": True,
            "file_type": "exr",
            "compression": "DWAA"
        }
        return knob_values

    @staticmethod
    def get_undistort_downscale_configuration() -> Tuple[Dict, int]:
        """
        You can write your custom logic for getting Undistort Write Node values.
        Method should return dict where key is knob name of Write Node.
        """
        knob_values = {
            "raw": True,
            "file_type": "exr",
            "compression": "DWAA"
        }
        downscale_width = 2048
        # downscale_height = 2048  # not implemented yet

        return knob_values, downscale_width

    @staticmethod
    def get_3d_camera_configuration() -> CameraConfig:
        """
        Determines how to adjust Camera configuration in .abc and .fbx files.
        MatchMoveExporter suggested that artist will work with undistorted
        plate in 3D software. To match Camera, Geo and Plate - we have to
        adjust focal or aperture.
        """
        return CameraConfig.ADJUST_FOCAL

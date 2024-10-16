"""
DO NOT IMPORT THIS FILE

This file is part of nuke_utilities. It used in get_export_pyscript() function.
"""
import nuke

import sys
import json

from lib.utilities.log_utilities import setup_or_get_logger
from lib.utilities.os_utilities import open_in_explorer


LOGGER = setup_or_get_logger(force_setup=True, use_console_handler=True)
LOGGER.info("Nuke started.")

NUKE_SCRIPT = sys.argv[1]
with open(sys.argv[2], "r") as file:
    JSON_DATA = json.load(file)


# TODO: create Cameras with Axis (if Axis needed)
# TODO: create Locators Group
# TODO: create PointGroups
# TODO: create Read files
# TODO: create Undistrot
# TODO: create STMap
# TODO: geo placement and import through TCL
# TODO: create Write and WriteGeo nodes + render

def animate_xyz_knob_values(knob: nuke.XYZ_Knob,
                            values: [[], [], []],  # [[x], [y], [z]]
                            first_frame: int = 1001):
    knob.setAnimated()
    for i, (x, y, z) in enumerate(zip(*values)):
        frame = first_frame + i
        knob.setValueAt(x, frame, 0)  # x
        knob.setValueAt(y, frame, 1)  # y
        knob.setValueAt(z, frame, 2)  # z

def animate_array_knob_values(knob: nuke.Array_Knob,
                              values: [],
                              first_frame: int = 1001):
    knob.setAnimated()
    for i, value in enumerate(values):
        frame = first_frame + i
        knob.setValueAt(value, frame)

def import_nodes_from_script(script_path: str) -> [nuke.Node]:
    previous_all_nodes = nuke.allNodes()
    nuke.scriptReadFile(script_path)
    return list(set(nuke.allNodes()) - set(previous_all_nodes))


def get_undistort_from_script(script_path: str) -> nuke.Node:
    undistorts = import_nodes_from_script(script_path)
    assert len(undistorts) == 1, f"In {script_path} supposed to be one node!"
    return undistorts[0]

def get_camera(camera_data: dict) -> nuke.Node:
    # create axis
    # PS: I haven't seen situation when axis needed -
    # don't implement now.

    # create camera, set knob values
    camera = nuke.nodes.Camera()
    camera["label"].setValue(camera_data['name'])

    for knob_name in ["translate", "rotate"]:
        animate_xyz_knob_values(knob=camera[knob_name],
                                values=[
                                    camera_data[knob_name]["x"],
                                    camera_data[knob_name]["y"],
                                    camera_data[knob_name]["z"]
                                ])
    animate_array_knob_values(knob=camera["focal"],
                              values=camera_data["focal"])
    camera["haperture"].setValue(camera_data["haperture"])
    camera["vaperture"].setValue(camera_data["vaperture"])

    return camera

def start():
    nuke.scriptOpen(NUKE_SCRIPT)

    for camera_data in JSON_DATA["cameras"]:
        camera = get_camera(camera_data)
        undistort = get_undistort_from_script(camera_data["undistort_script_path"])

        # create source
        # STOP THERE!

        pass

    nuke.scriptSave(NUKE_SCRIPT)


start()

open_in_explorer(NUKE_SCRIPT)

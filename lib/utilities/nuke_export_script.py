"""
DO NOT IMPORT THIS FILE

This file is part of nuke_utilities. It used in get_export_pyscript() function.
"""
import os.path
import shutil

import nuke

import sys
import json
from random import random

from lib.utilities.log_utilities import setup_or_get_logger
from lib.utilities.os_utilities import open_in_explorer
from lib.utilities.nuke_utilities import import_file_as_read_node


# config start
GEO_FOLDER_NAME = "geo"
# config end


LOGGER = setup_or_get_logger(force_setup=True, use_console_handler=True)
LOGGER.info("Nuke started.")

NUKE_SCRIPT = sys.argv[1]
with open(sys.argv[2], "r") as file:
    JSON_DATA = json.load(file)

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
    undistort = undistorts[0]
    undistort["label"].setValue(undistort.name().replace("LD_3DE4_", ""))
    undistort.setName("UNDISTORT")
    return undistorts

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
                                    camera_data[knob_name]["xs"],
                                    camera_data[knob_name]["ys"],
                                    camera_data[knob_name]["zs"]
                                ])
    animate_array_knob_values(knob=camera["focal"],
                              values=camera_data["focal"])
    camera["haperture"].setValue(camera_data["haperture"])
    camera["vaperture"].setValue(camera_data["vaperture"])

    return camera

def create_grade_node(camera_data: dict, connect_to: nuke.Node = None) -> nuke.Node:
    grade = nuke.nodes.Grade()
    if connect_to:
        grade.setInput(0, connect_to)
    grade["blackpoint"].setValue(camera_data["source"]["black_white"][0])
    grade["whitepoint"].setValue(camera_data["source"]["black_white"][1])
    grade["gamma"].setValue(camera_data["source"]["gamma"])
    return grade

def create_soft_clip_node(camera_data: dict, connect_to: nuke.Node = None) -> nuke.Node:
    softclip = nuke.nodes.SoftClip()
    if connect_to:
        softclip.setInput(0, connect_to)
    softclip["softclip_min"].setValue(1 - camera_data["source"]["softclip"])
    softclip["softclip_max"].setValue(16)
    return softclip


def create_node(class_: str, connect_to: nuke.Node = None, knobs: dict = None) -> nuke.Node:
    try:
        node = getattr(nuke.nodes, class_)()
    except AttributeError:
        raise ValueError(f"Node class '{class_}' does not exist in nuke.nodes")

    if connect_to:
        node.setInput(0, connect_to)

    if knobs:
        for knob, value in knobs.items():
            if type(value) is str and value.startswith("[") and value.endswith("]"):
                node[knob].setExpression(value)
            else:
                node[knob].setValue(value)

    return node


def create_read_geo_node(geo_path: str) -> nuke.Node:
    read_geo = nuke.createNode('ReadGeo2', "file {" + geo_path + "}", inpanel=False)
    read_geo["file"].setValue(f"[file dirname [value root.name]]/{GEO_FOLDER_NAME}/{os.path.basename(geo_path)}")

    for knob in ["display", "render_mode"]:
        read_geo[knob].setValue("wireframe")

    return read_geo


def create_read_geo_nodes() -> list:
    read_geo_nodes = []

    common_geo_path = os.path.join(os.path.dirname(NUKE_SCRIPT), GEO_FOLDER_NAME)
    os.makedirs(common_geo_path, exist_ok=True)
    for geo_path in JSON_DATA["geo"]:
        LOGGER.info(geo_path)
        if not os.path.exists(geo_path):
            continue
        new_geo_path = shutil.copy2(geo_path, common_geo_path)
        read_geo_nodes.append(create_read_geo_node(new_geo_path))

    return read_geo_nodes


def create_group_for_points(name: str) -> nuke.Node:
    group = nuke.nodes.Group()
    group.setName(name)
    slider_knob = nuke.Double_Knob("sphere_radius", "Sphere Radius:")
    slider_knob.setValue(1), slider_knob.setRange(0, 10)
    group.addKnob(slider_knob)
    return group


def get_locators_group() -> nuke.Node:
    locator_group = create_group_for_points("Locators")

    with locator_group:  # go inside Group
        sphere = create_node("Sphere", knobs={"rows": 3, "columns": 3, "radius": "[value parent.sphere_radius]"})
        merge_geo = nuke.nodes.MergeGeo()

        for i, locator_data in enumerate(JSON_DATA["locators"]):
            constant = create_node("Constant", knobs={"color": [random(), random(), random(), 1]})
            sphere_copy = nuke.clone(sphere)
            sphere_copy.setInput(0, constant)
            x, y, z = locator_data["x_pos"], locator_data["y_pos"], locator_data["z_pos"]
            transform_geo = create_node("TransformGeo", knobs={"translate": [x, y, z]})
            transform_geo.setName(f"Locator_{locator_data['name']}")
            transform_geo.setInput(0, sphere_copy)
            merge_geo.setInput(i, transform_geo)

        create_node("Output", merge_geo)

    return locator_group


def get_point_groups():

    for point_group_data in JSON_DATA["point_groups"]:
        point_group = create_group_for_points("PointGroup")

        with point_group:
            pass  # STOP THERE!

    return point_group


def start():
    nuke.scriptOpen(NUKE_SCRIPT)

    for camera_data in JSON_DATA["cameras"]:
        camera = get_camera(camera_data)
        undistort = get_undistort_from_script(camera_data["undistort_script_path"])
        read = import_file_as_read_node(camera_data["source"]["path"])
        softclip = create_soft_clip_node(camera_data, read)
        grade = create_grade_node(camera_data, softclip)
        colorspace_node = create_node("Colorspace", grade, {"colorspace_in": "sRGB"})

    locators = get_locators_group()

    read_geo_nodes = create_read_geo_nodes()

    # point groups
    point_groups = get_point_groups()

    nuke.scriptSave(NUKE_SCRIPT)


start()


open_in_explorer(NUKE_SCRIPT)
# TODO: create Cameras with Axis (if Axis needed) +
# TODO: create Locators Group +
# TODO: create PointGroups
# TODO: create Read files +
# TODO: create Undistrot +
# TODO: create STMap
# TODO: make sure 3DE4 Undistort nodes exists in Nuke
# TODO: geo placement and import through TCL
# TODO: set Root settings
# TODO: create Write and WriteGeo nodes + render


# set cut_paste_input [stack 0]
# version 14.0 v7
# push $cut_paste_input
# Grade {
#  gamma 1.5
#  black_clamp false
#  name Grade2
#  selected true
#  xpos 440
#  ypos 103
# }
# SoftClip {
#  softclip_min 0.5
#  softclip_max 16
#  name SoftClip1
#  selected true
#  xpos 440
#  ypos 129
# }
# Colorspace {
#  colorspace_in sRGB
#  name Colorspace1
#  selected true
#  xpos 440
#  ypos 155
# }

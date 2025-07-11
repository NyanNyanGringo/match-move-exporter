"""
DO NOT IMPORT THIS FILE

This file is part of nuke_utilities. It used in get_export_pyscript() function.
"""
from typing import Literal

import nuke

import os
import shutil
import json
from random import random

from MatchMoveExporter.lib.utilities.log_utilities import setup_or_get_logger
from MatchMoveExporter.lib.utilities.os_utilities import open_in_explorer
from MatchMoveExporter.lib.utilities.nuke_utilities import import_file_as_read_node, import_nodes_from_script, \
    animate_array_knob_values, animate_xyz_knob_values
from MatchMoveExporter.lib.utilities.userconfig_utilities import CameraConfig
from MatchMoveExporter.lib.utilities.name_convention_utilities import get_name_from_filepath, insert_layer, get_version
from MatchMoveExporter.userconfig import UserConfig
from MatchMoveExporter.lib.utilities import config_utilities
from MatchMoveExporter.lib.utilities.config_utilities import ConfigKeys


# setup logger from lib


LOGGER = setup_or_get_logger(force_setup=True, use_console_handler=True)
if os.getenv("DEV"):
    LOGGER.info(f"Nuke started in DEV mode.")
else:
    LOGGER.info(f"Nuke started.")


# get nuke script and json data from system arguments


NUKE_SCRIPT = os.getenv("NUKE_SCRIPT_PATH")
with open(os.getenv("JSON_FOR_NUKE_PATH"), "r") as file:
    JSON_DATA = json.load(file)

# reduce the range of frames when develop


# if os.getenv("DEV"):
#     range_ = JSON_DATA["range"]
#     JSON_DATA["range"] = [range_[0], 2]
#     del range_


# some global variables


OFFSET = JSON_DATA["offset"]  # usually 1001
ORIGINAL_FIRST, ORIGINAL_LAST, STEP = JSON_DATA["original_range"]  # original range that was used from source
if JSON_DATA["calculation_range"]:  # range of final calculation
    FIRST_FRAME = JSON_DATA["calculation_range"][0] + OFFSET - 1
    LAST_FRAME = JSON_DATA["calculation_range"][1] + OFFSET - 1
else:
    FIRST_FRAME = OFFSET
    LAST_FRAME = OFFSET + ORIGINAL_LAST - ORIGINAL_FIRST

LOGGER.info(f"First: {FIRST_FRAME}. Last: {LAST_FRAME}. Offset: {OFFSET}.")


# functions


def _get_filepath_for_write(folder_name: str = None, intermediate_name: str = None, layer_name: str = None) -> str:
    """Return filepath for Write Node without padding and extenstion."""
    name = get_name_from_filepath(NUKE_SCRIPT)
    return os.path.join(
        os.path.dirname(NUKE_SCRIPT),
        intermediate_name if intermediate_name else "",
        folder_name if folder_name else "",
        insert_layer(name, layer_name) if layer_name else name
    ).replace("\\", "/")


# nodes functions


def _setup_read_node(read_node: nuke.Node) -> nuke.Node:
    read_node["colorspace"].setValue(UserConfig.get_read_node_colorspace(read_node["file"].value()))

    read_node["first"].setValue(ORIGINAL_FIRST)
    read_node["last"].setValue(ORIGINAL_LAST)

    read_node["frame_mode"].setValue("start at")
    read_node["frame"].setValue(str(OFFSET))

    return read_node

def _create_node(class_: str, connect_to: nuke.Node = None, knobs: dict = None) -> nuke.Node:
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

def _get_undistort_from_script(script_path: str) -> [nuke.Node]:
    [n.setSelected(False) for n in nuke.allNodes()]

    undistorts = import_nodes_from_script(script_path)
    assert len(undistorts) == 1, f"Inside {script_path} supposed to be one node!"
    undistort = undistorts[0]
    undistort["label"].setValue(undistort.name().replace("LD_3DE4_", ""))
    undistort.setName("UNDISTORT")

    return undistorts

def _copy_nk_undistort_file(undistort_filepath: str, intermediate_name: str = None):
    if JSON_DATA["program"] == "3DE4" and UserConfig.export_undistort_nk_project:
        new_filepath = _get_filepath_for_write(
            folder_name=None,
            intermediate_name=intermediate_name,
            layer_name=UserConfig.undistort_nk_project_name
        ) + ".nk"
        os.makedirs(os.path.dirname(new_filepath), exist_ok=True)
        shutil.copy2(undistort_filepath, new_filepath)

def _get_camera(camera_data: dict, read_node: nuke.Node = None,
                undistort: nuke.Node = None, for_3d_export:bool = False) -> nuke.Node:
    """
    Create Camera3 nuke.Node according to camera_data from 3DEqualizer.

    :param camera_data: data from 3D equalizer about Camera.
    :param read_node: Nuke Read node to take dimensions for focal length from.
    :param for_3d_export: if True, converts focal length to work with undistorted + reformatted image.
    :return: nuke.Node
    """
    # create axis
    # PS: I haven't seen situation when axis needed -
    # don't implement now.
    # 2880/3231*curve
    # create camera, set knob values
    camera = _create_node("Camera3")
    camera["label"].setValue(camera_data['name'])

    for knob_name in ["translate", "rotate"]:
        animate_xyz_knob_values(knob=camera[knob_name],
                                values=[
                                    camera_data[knob_name]["xs"],
                                    camera_data[knob_name]["ys"],
                                    camera_data[knob_name]["zs"]
                                ],
                                first_frame=OFFSET)
    animate_array_knob_values(knob=camera["focal"],
                              values=camera_data["focal"],
                              first_frame=OFFSET)
    camera["haperture"].setValue(camera_data["haperture"])
    camera["vaperture"].setValue(camera_data["vaperture"])

    if for_3d_export:
        undistort_copy = nuke.clone(undistort)
        crop_with_reformat = _create_crop_with_reformat()

        undistort_copy.setInput(0, read_node)
        crop_with_reformat.setInput(0, undistort_copy)

        box: tuple = crop_with_reformat["box"].value()
        width_with_undistort = abs(box[0]) + abs(box[2])

        camera_config = UserConfig.get_3d_camera_configuration()
        if camera_config == CameraConfig.ADJUST_FOCAL:
            camera["focal"].setExpression(f"{camera_data['width']} / {width_with_undistort} * curve")
        elif camera_config == CameraConfig.ADJUST_APERTURE:
            camera["haperture"].setExpression(f"{width_with_undistort} / {camera_data['width']} * {camera_data['haperture']}")
            camera["vaperture"].setExpression(f"{width_with_undistort} / {camera_data['width']} * {camera_data['vaperture']}")

        nuke.delete(undistort_copy)
        nuke.delete(crop_with_reformat)

    return camera

def _create_grade_node(camera_data: dict, connect_to: nuke.Node = None) -> nuke.Node:
    grade = _create_node("Grade")
    if connect_to:
        grade.setInput(0, connect_to)
    grade["blackpoint"].setValue(camera_data["source"]["black_white"][0])
    grade["whitepoint"].setValue(camera_data["source"]["black_white"][1])
    grade["gamma"].setValue(camera_data["source"]["gamma"])
    return grade

def _create_soft_clip_node(camera_data: dict, connect_to: nuke.Node = None) -> nuke.Node:
    softclip = nuke.nodes.SoftClip()
    if connect_to:
        softclip.setInput(0, connect_to)
    softclip["softclip_min"].setValue(1 - camera_data["source"]["softclip"])
    softclip["softclip_max"].setValue(16)
    return softclip

def _create_read_geo_node(geo_path: str) -> nuke.Node:
    read_geo = nuke.createNode('ReadGeo2', "file {" + geo_path + "}", inpanel=False)
    geo_folder_path = UserConfig.get_geo_folder_name()
    read_geo["file"].setValue(f"[file dirname [value root.name]]/{geo_folder_path}/{os.path.basename(geo_path)}")

    for knob in ["display", "render_mode"]:
        read_geo[knob].setValue("wireframe")

    return read_geo

def _create_read_geo_nodes(geo_paths: list) -> list:
    read_geo_nodes = []

    common_geo_path = os.path.join(os.path.dirname(NUKE_SCRIPT), UserConfig.get_geo_folder_name())
    if geo_paths:
        os.makedirs(common_geo_path, exist_ok=True)
    for geo_path in geo_paths:
        if not os.path.exists(geo_path):
            LOGGER.info(f"Geo doesn't exists: {geo_path}")
            continue
        new_geo_path = shutil.copy2(geo_path, common_geo_path)
        read_geo = _create_read_geo_node(new_geo_path)
        read_geo_nodes.append(read_geo)

    return read_geo_nodes

def _create_group_for_points(name: str) -> nuke.Node:
    group = nuke.nodes.Group()
    group.setName(name)
    slider_knob = nuke.Double_Knob("sphere_radius", "Sphere Radius:")
    slider_knob.setValue(1), slider_knob.setRange(0, 10)
    group.addKnob(slider_knob)
    return group

def _get_point_groups() -> [nuke.Node]:
    # TODO: shuffle all the nodes + backdrop
    point_groups = []

    for point_group_data in JSON_DATA["point_groups"]:
        point_group_type = point_group_data["type"]  # CAMERA or OBJECT
        name = f"CameraGeoGroup" if point_group_type == "CAMERA" else "ObjectGeoGroup"
        point_group = _create_group_for_points(name)

        with point_group:  # go inside Group
            sphere = _create_node("Sphere", knobs={"rows": 3, "columns": 3, "radius": "[value parent.sphere_radius]"})
            merge_geo = nuke.nodes.MergeGeo()

            axis = nuke.nodes.Axis3()
            axis.setName(f"Axis_{point_group_data['name']}")
            axis_data = point_group_data["axis"]
            for knob_name in ["translate", "rotate"]:

                animate_xyz_knob_values(knob=axis[knob_name],
                                        values=[
                                            axis_data[knob_name]["xs"],
                                            axis_data[knob_name]["ys"],
                                            axis_data[knob_name]["zs"]
                                        ],
                                        first_frame=OFFSET)

            last_merge_geo_input = 0
            geo_nodes = _create_read_geo_nodes(point_group_data["geo"])
            for i, geo_node in enumerate(geo_nodes):
                if point_group_type == "OBJECT":
                    transform_geo = _create_node("TransformGeo")
                    transform_geo.setInput(0, geo_node)
                    transform_geo.setInput(1, axis)
                    merge_geo.setInput(i, transform_geo)
                else:
                    merge_geo.setInput(i, geo_node)

                last_merge_geo_input = i

            sphere_copy = None
            for i, point_data in enumerate(point_group_data["points"]):
                constant = _create_node("Constant", knobs={"color": [random(), random(), random(), 1]})
                if sphere_copy:
                    sphere_copy = nuke.clone(sphere)
                else:
                    sphere_copy = sphere
                sphere_copy.setInput(0, constant)
                x, y, z = point_data["x_pos"], point_data["y_pos"], point_data["z_pos"]
                transform_geo = _create_node("TransformGeo", knobs={"translate": [x, y, z]})
                transform_geo.setName(f"Point_{point_data['name']}")
                transform_geo.setInput(0, sphere_copy)
                transform_geo.setInput(1, axis)

                merge_geo.setInput(i + last_merge_geo_input + 1, transform_geo)

            _create_node("Output", merge_geo)

            if point_group_type == "CAMERA":
                nuke.delete(axis)

        point_groups.append(point_group)

    return point_groups

def _set_root_settings():
    fps = JSON_DATA["fps"]
    width = JSON_DATA["width"]
    height = JSON_DATA["height"]

    format_name = f"{width}x{height}"
    nuke.addFormat(f"{width} {height} 1.0 {format_name}")
    nuke.Root()["format"].setValue(format_name)

    nuke.Root()["fps"].setValue(fps)
    nuke.Root()["first_frame"].setValue(FIRST_FRAME)
    nuke.Root()["last_frame"].setValue(LAST_FRAME)
    nuke.Root()["lock_range"].setValue(True)

    colorManagement, OCIO_config = UserConfig.get_color_manager_and_config()
    nuke.Root()["colorManagement"].setValue(colorManagement)
    nuke.Root()["OCIO_config"].setValue(OCIO_config)
    nuke.Root()["reloadConfig"].execute()

def _create_stmap_node() -> nuke.Node:
    stmap = _create_node("Expression", knobs={"expr0": "x/(width-1)", "expr1": "y/(height-1)", "expr2": "0"})
    stmap.setName("STmap")
    return stmap

def _create_crop_with_reformat() -> nuke.Node:
    crop = _create_node("Crop")
    crop["box"].setExpression("bbox.x", 0)
    crop["box"].setExpression("bbox.y", 1)
    crop["box"].setExpression("bbox.r", 2)
    crop["box"].setExpression("bbox.t", 3)
    crop["reformat"].setValue(1)
    return crop

def _create_crop() -> nuke.Node:
    crop = _create_node("Crop")
    crop["box"].setExpression("width", 2)
    crop["box"].setExpression("height", 3)
    return crop

def _create_write_dailies(intermediate_name: str = None) -> nuke.Node:
    write = _create_node("Write")
    filepath = "[file dirname [value root.name]]/"
    if intermediate_name:
        filepath += f"{intermediate_name}/"
    filepath += "[file rootname [basename [value root.name]]].mov"
    write["file"].setValue(filepath)
    write["file_type"].setValue("mov")
    write["mov64_codec"].setValue("h264")
    write["mov64_fps"].setExpression("[value root.fps]")
    write["mov64_bitrate"].setValue(20000)
    write["create_directories"].setValue(True)
    write["first"].setValue(FIRST_FRAME)
    write["last"].setValue(LAST_FRAME)
    write["use_limit"].setValue(True)

    for knob_name, value in UserConfig.get_dailies_configuration().items():
        write[knob_name].setValue(value)

    return write

def _create_write_stmap(intermediate_name: str = None, lens_is_static: bool = False) -> nuke.Node:
    write = _create_node("Write")

    filepath = _get_filepath_for_write(folder_name="stmap",
                                       intermediate_name=intermediate_name,
                                       layer_name="stmap") + ".####.exr"

    write["file"].setValue(filepath)
    write["raw"].setValue(True)
    write["file_type"].setValue("exr")
    write["compression"].setValue("Zip")
    write["create_directories"].setValue(True)
    write["first"].setValue(FIRST_FRAME)
    if lens_is_static:
        write["last"].setValue(FIRST_FRAME)
    else:
        write["last"].setValue(LAST_FRAME)
    write["use_limit"].setValue(True)

    LOGGER.info(filepath)

    return write

def _create_write_undistort(intermediate_name: str = None) -> nuke.Node:
    write = _create_node("Write")

    filepath = _get_filepath_for_write(folder_name="undistort",
                                       intermediate_name=intermediate_name,
                                       layer_name="undistort") + ".####."

    write["create_directories"].setValue(True)
    write["first"].setValue(FIRST_FRAME)
    write["last"].setValue(LAST_FRAME)
    write["use_limit"].setValue(True)

    for knob_name, value in UserConfig.get_undistort_configuration().items():
        write[knob_name].setValue(value)

        if knob_name == "file_type":
            filepath += value

    write["file"].setValue(filepath)

    LOGGER.info(filepath)

    return write

def _create_write_undistort_downscale(intermediate_name: str = None) -> nuke.Node:
    write = _create_node("Write")

    filepath = _get_filepath_for_write(folder_name="undistort_downscale",
                                       intermediate_name=intermediate_name,
                                       layer_name="undistort_downscale") + ".####."

    write["create_directories"].setValue(True)
    write["first"].setValue(FIRST_FRAME)
    write["last"].setValue(LAST_FRAME)
    write["use_limit"].setValue(True)

    for knob_name, value in UserConfig.get_undistort_downscale_configuration()[0].items():
        write[knob_name].setValue(value)

        if knob_name == "file_type":
            filepath += value

    write["file"].setValue(filepath)

    LOGGER.info(filepath)

    return write

def _create_write_geo(file_type: str, intermediate_name: str = None, layer_name: str = None) -> nuke.Node:

    if not file_type in ["abc", "fbx"]:
        raise ValueError("File type must be abc or fbx.")

    write_geo = _create_node("WriteGeo")

    filepath = _get_filepath_for_write(intermediate_name=intermediate_name, layer_name=layer_name) + f".{file_type}"

    write_geo["file"].setValue(filepath)
    write_geo["first"].setValue(FIRST_FRAME)
    write_geo["last"].setValue(LAST_FRAME)
    write_geo["use_limit"].setValue(True)
    write_geo["file_type"].setValue(file_type)
    if file_type == "abc":
        write_geo["storageFormat"].setValue("Ogawa")
    if file_type == "fbx":
        write_geo["animateMeshVertices"].setValue(True)
    return write_geo


# render functions


def _render_dailies(from_node: nuke.Node, intermediate_name: str = None, cleanup_after_render: bool = False,
                    dailies_gizmo: nuke.Node = None) -> None:
    crop_reformat = _create_crop_with_reformat()
    reformat = _create_node("Reformat", knobs={"type": "to box", "box_width": 2048})
    crop = _create_crop()
    write = _create_write_dailies(intermediate_name)
    nodes_to_cleanup = [crop, reformat, crop_reformat, write]

    crop_reformat.setInput(0, from_node)
    reformat.setInput(0, crop_reformat)
    crop.setInput(0, reformat)
    write.setInput(0, crop)

    x_pos, y_pos, space = from_node.xpos(), from_node.ypos(), 1
    crop_reformat.setXYpos(x_pos, y_pos + 100 * space)
    reformat.setXYpos(x_pos, y_pos + 130 * space)
    crop.setXYpos(x_pos, y_pos + 173 * space)
    write.setXYpos(x_pos, y_pos + 305 * space)

    if dailies_gizmo:
        dailies_gizmo.setInput(0, crop)
        dailies_gizmo.setXYpos(x_pos, y_pos + 205 * space)
        write.setInput(0, dailies_gizmo)

    nuke.render(write)

    if cleanup_after_render:
        for n in nodes_to_cleanup:
            nuke.delete(n)

def _render_stmap(from_node: nuke.Node, undistort: nuke.Node, intermediate_name: str = None,
                  lens_is_static: bool = False) -> None:
    stmap = _create_stmap_node()
    crop = _create_crop()
    undistort_copy = nuke.clone(undistort)
    crop_reformat = _create_crop_with_reformat()
    write = _create_write_stmap(intermediate_name, lens_is_static)
    nodes_to_cleanup = [stmap, crop, undistort_copy, crop_reformat, write]

    stmap.setInput(0, from_node)
    crop.setInput(0, stmap)
    undistort_copy.setInput(0, crop)
    crop_reformat.setInput(0, undistort_copy)
    write.setInput(0, crop_reformat)

    nuke.render(write)

    for n in nodes_to_cleanup:
        nuke.delete(n)

def _render_undistort(from_node: nuke.Node, intermediate_name: str = None) -> None:
    crop_reformat = _create_crop_with_reformat()
    write = _create_write_undistort(intermediate_name)
    nodes_to_cleanup = [crop_reformat, write]

    crop_reformat.setInput(0, from_node)
    write.setInput(0, crop_reformat)

    nuke.render(write)

    for n in nodes_to_cleanup:
        nuke.delete(n)

def _render_undistort_downscale(from_node: nuke.Node, intermediate_name: str = None) -> None:
    _, downscale_width = UserConfig.get_undistort_downscale_configuration()

    crop_reformat = _create_crop_with_reformat()
    reformat = _create_node("Reformat", knobs={"type": "to box", "box_width": downscale_width})
    write = _create_write_undistort_downscale(intermediate_name)
    nodes_to_cleanup = [crop_reformat, reformat, write]

    crop_reformat.setInput(0, from_node)
    reformat.setInput(0, crop_reformat)
    write.setInput(0, reformat)

    nuke.render(write)

    for n in nodes_to_cleanup:
        nuke.delete(n)

def _render_geo(from_node: nuke.Node, intermediate_name: str, file_type: str, layer_name: str = None) -> None:

    if not file_type in ["abc", "fbx"]:
        raise ValueError("File type must be abc or fbx.")

    write_geo = _create_write_geo(file_type, intermediate_name, layer_name)

    write_geo.setInput(0, from_node)

    os.makedirs(os.path.dirname(write_geo["file"].value()), exist_ok=True)
    nuke.render(write_geo)

    nuke.delete(write_geo)


# shuffle function


def _get_intermediate_name(name: str, index: int):
    return name if index else None


def _shuffle_and_render_nodes(nodes_data) -> None:
    """
    nodes_data = {
        "read_groups": [
            {
                "camera": nuke.Node
                "read": nuke.Node,
                "undistort": nuke.Node,
                "stmap": nuke.Node,
                "camera_data": dict
            }
        },
        "geo_nodes: [nuke.Node, ...]
        ""
    }
    """
    # scene + geo nodes
    scene = _create_node("Scene")
    scene.setXYpos(0, 0)
    for i, geo_node in enumerate(nodes_data["geo_nodes"]):
        scene.setInput(i, geo_node)
        geo_node.setXYpos(i * 150 * -1 - 10, -100)  # -10 is offset to align to scene node

    # create read groups
    x_offset = 0
    for index, read_group in enumerate(nodes_data["read_groups"]):
        x_pos, y_pos = 200 + x_offset, -100

        # read
        read = read_group["read"]
        read.setXYpos(x_pos, y_pos)

        # crop
        crop = _create_crop()
        crop.setInput(0, read)
        y_pos += 96
        crop.setXYpos(x_pos, y_pos)

        # undistort
        undistort = read_group["undistort"]
        undistort.setInput(0, crop)
        y_pos += 60
        undistort.setXYpos(x_pos, y_pos)

        # dot + scanline + camera + merge
        y_pos += 120

        dot = _create_node("Dot", undistort)
        dot.setXYpos(x_pos + 34, y_pos + 4)

        camera = read_group["camera"]
        camera.setXYpos(x_pos - 400, y_pos - 20)

        scanline = _create_node("ScanlineRender", knobs={"motion_vectors_type": "off", "overscan": 500})
        scanline.setInput(0, dot)
        scanline.setInput(1, scene)
        scanline.setInput(2, camera)
        scanline.setXYpos(x_pos - 210, y_pos)

        merge = _create_node("Merge2", knobs={"bbox": "B"})
        merge.setInput(0, dot)
        merge.setInput(1, scanline)
        merge.setXYpos(x_pos, y_pos + 80)

        # offset for next read_group
        x_offset += 500

        # get intermediate_name
        intermediate_name = _get_intermediate_name(read_group["camera_data"]["name"], index)

        # render geo
        camera_for_3d_export = read_group["camera_for_3d_export"]
        file_types = ["abc"] * UserConfig.export_abc + ["fbx"] * UserConfig.export_fbx
        for file_type in file_types:
            if UserConfig.separate_cam_and_geo:
                _render_geo(from_node=scene, intermediate_name=intermediate_name, file_type=file_type, layer_name="geo")
                camera_scene = _create_node("Scene", connect_to=camera_for_3d_export)
                _render_geo(from_node=camera_scene, intermediate_name=intermediate_name, file_type=file_type, layer_name="camera")
                nuke.delete(camera_scene)
            else:
                scene.setInput(scene.inputs(), camera_for_3d_export)
                _render_geo(from_node=scene, intermediate_name=intermediate_name, file_type=file_type)
                scene.setInput(scene.inputs() - 1, None)

        nuke.delete(camera_for_3d_export)

        # render stmap, undistort and dailies
        if UserConfig.export_stmap:
            _render_stmap(from_node=crop, undistort=undistort, intermediate_name=intermediate_name,
                          lens_is_static=read_group["camera_data"]["lens_is_static"])
        if UserConfig.export_undistort:
            _render_undistort(from_node=undistort, intermediate_name=intermediate_name)
        if UserConfig.export_undistort_downscale:
            _render_undistort_downscale(from_node=undistort, intermediate_name=intermediate_name)
        if UserConfig.export_dailies:
            _render_dailies(from_node=merge, intermediate_name=intermediate_name, dailies_gizmo=read_group["dailies_gizmo"])


# start


def _start():

    nuke.scriptSave(NUKE_SCRIPT)  # save to crete file
    nuke.scriptOpen(NUKE_SCRIPT)

    _set_root_settings()

    read_groups = []
    for index, camera_data in enumerate(JSON_DATA["cameras"]):
        read = _setup_read_node(import_file_as_read_node(camera_data["source"]["path"]))
        version = get_version(nuke.Root().name())
        LOGGER.info(f"Version: {version}")
        project = None
        if config_utilities.check_key(ConfigKeys.PROJECT):
            project = config_utilities.read_config_key(ConfigKeys.PROJECT)
        username = None
        if config_utilities.check_key(ConfigKeys.USERNAME):
            username = config_utilities.read_config_key(ConfigKeys.USERNAME)
        gizmo_class, gizmo_knob_values = UserConfig.setup_dailies_gizmo(get_name_from_filepath(nuke.Root().name()),
                                                                        version,
                                                                        project,
                                                                        username)
        dailies_gizmo = _create_node(gizmo_class, knobs=gizmo_knob_values) if gizmo_class else None
        undistort = _get_undistort_from_script(camera_data["undistort_script_path"])[0]
        camera = _get_camera(camera_data)
        camera_for_3d_export = _get_camera(camera_data, read_node=read, undistort=undistort, for_3d_export=True)
        _copy_nk_undistort_file(
            camera_data["undistort_script_path"],
            intermediate_name=_get_intermediate_name(camera_data["name"], index)
        )

        read_groups.append({
            "camera": camera,
            "camera_for_3d_export": camera_for_3d_export,
            "read": read,
            "dailies_gizmo": dailies_gizmo,
            "undistort": undistort,
            # "name": camera_data["name"],
            # "lens_is_static": camera_data["lens_is_static"],
            "camera_data": camera_data
        })

    point_groups = _get_point_groups()

    # shuffle nodes
    nodes_data = {
        "read_groups": read_groups,
        "geo_nodes": point_groups
    }
    _shuffle_and_render_nodes(nodes_data)

    [nuke.delete(node) for node in nuke.allNodes() if node.Class() == "Viewer"]

    if JSON_DATA["program"] == "3DE4" and UserConfig.export_tde4_project:
        shutil.copy2(JSON_DATA["3de4_project_path"], os.path.dirname(NUKE_SCRIPT))

    if JSON_DATA["program"] == "3DE4" and UserConfig.export_maya:
        shutil.copy2(JSON_DATA["maya_project_path"], os.path.join(
            os.path.dirname(NUKE_SCRIPT),
            get_name_from_filepath(NUKE_SCRIPT) + ".mel"
        ))

    nuke.scriptSave(NUKE_SCRIPT)

    open_in_explorer(NUKE_SCRIPT)

    if not UserConfig.export_nk_project:
        os.remove(NUKE_SCRIPT)


try:
 _start()
except Exception as e:
    LOGGER.info(e)

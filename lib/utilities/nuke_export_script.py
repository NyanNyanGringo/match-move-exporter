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
if os.getenv("DEV"):
    LOGGER.info(f"Nuke started in DEV mode.")
else:
    LOGGER.info(f"Nuke started.")

NUKE_SCRIPT = sys.argv[1]
with open(sys.argv[2], "r") as file:
    JSON_DATA = json.load(file)

if os.getenv("DEV"):
    range_ = JSON_DATA["range"]
    JSON_DATA["range"] = [range_[0], 2]
    del range_

OFFSET = JSON_DATA["offset"]
FIRST_FRAME = JSON_DATA["range"][0] + OFFSET - 1
LAST_FRAME = JSON_DATA["range"][1] + OFFSET - 1

def animate_xyz_knob_values(knob: nuke.XYZ_Knob,
                            values: [[], [], []],  # [[x], [y], [z]]
                            first_frame: int = OFFSET):
    knob.setAnimated()
    for i, (x, y, z) in enumerate(zip(*values)):
        frame = first_frame + i
        knob.setValueAt(x, frame, 0)  # x
        knob.setValueAt(y, frame, 1)  # y
        knob.setValueAt(z, frame, 2)  # z

def animate_array_knob_values(knob: nuke.Array_Knob,
                              values: [],
                              first_frame: int = OFFSET):
    knob.setAnimated()
    for i, value in enumerate(values):
        frame = first_frame + i
        knob.setValueAt(value, frame)

def import_nodes_from_script(script_path: str) -> [nuke.Node]:
    previous_all_nodes = nuke.allNodes()
    nuke.scriptReadFile(script_path)
    return list(set(nuke.allNodes()) - set(previous_all_nodes))


def get_undistort_from_script(script_path: str) -> [nuke.Node]:
    [n.setSelected(False) for n in nuke.allNodes()]
    undistorts = import_nodes_from_script(script_path)
    assert len(undistorts) == 1, f"Inside {script_path} supposed to be one node!"
    undistort = undistorts[0]
    undistort["label"].setValue(undistort.name().replace("LD_3DE4_", ""))
    undistort.setName("UNDISTORT")
    return undistorts

def get_camera(camera_data: dict) -> nuke.Node:
    # create axis
    # PS: I haven't seen situation when axis needed -
    # don't implement now.

    # create camera, set knob values
    camera = create_node("Camera3")
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


def create_read_geo_nodes(geo_paths: list) -> list:
    read_geo_nodes = []

    common_geo_path = os.path.join(os.path.dirname(NUKE_SCRIPT), GEO_FOLDER_NAME)
    os.makedirs(common_geo_path, exist_ok=True)
    for geo_path in geo_paths:
        if not os.path.exists(geo_path):
            LOGGER.info(f"Geo doesn't exists: {geo_path}")
            continue
        new_geo_path = shutil.copy2(geo_path, common_geo_path)
        read_geo = create_read_geo_node(new_geo_path)
        read_geo_nodes.append(read_geo)

    return read_geo_nodes


def create_group_for_points(name: str) -> nuke.Node:
    group = nuke.nodes.Group()
    group.setName(name)
    slider_knob = nuke.Double_Knob("sphere_radius", "Sphere Radius:")
    slider_knob.setValue(1), slider_knob.setRange(0, 10)
    group.addKnob(slider_knob)
    return group


def get_point_groups() -> [nuke.Node]:
    # TODO: shuffle all the nodes + backdrop
    point_groups = []

    for point_group_data in JSON_DATA["point_groups"]:
        point_group_type = point_group_data["type"]  # CAMERA or OBJECT
        name = f"CameraGeoGroup" if point_group_type == "CAMERA" else "ObjectGeoGroup"
        point_group = create_group_for_points(name)

        with point_group:  # go inside Group
            sphere = create_node("Sphere", knobs={"rows": 3, "columns": 3, "radius": "[value parent.sphere_radius]"})
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
                                        ])

            last_merge_geo_input = 0
            geo_nodes = create_read_geo_nodes(point_group_data["geo"])
            for i, geo_node in enumerate(geo_nodes):
                if point_group_type == "OBJECT":
                    transform_geo = create_node("TransformGeo")
                    transform_geo.setInput(0, geo_node)
                    transform_geo.setInput(1, axis)
                    merge_geo.setInput(i, transform_geo)
                else:
                    merge_geo.setInput(i, geo_node)

                last_merge_geo_input = i

            sphere_copy = None
            for i, point_data in enumerate(point_group_data["points"]):
                constant = create_node("Constant", knobs={"color": [random(), random(), random(), 1]})
                if sphere_copy:
                    sphere_copy = nuke.clone(sphere)
                else:
                    sphere_copy = sphere
                sphere_copy.setInput(0, constant)
                x, y, z = point_data["x_pos"], point_data["y_pos"], point_data["z_pos"]
                transform_geo = create_node("TransformGeo", knobs={"translate": [x, y, z]})
                transform_geo.setName(f"Point_{point_data['name']}")
                transform_geo.setInput(0, sphere_copy)
                transform_geo.setInput(1, axis)

                merge_geo.setInput(i + last_merge_geo_input + 1, transform_geo)

            create_node("Output", merge_geo)

            if point_group_type == "CAMERA":
                nuke.delete(axis)

        point_groups.append(point_group)

    return point_groups


def set_root_settings():
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

def create_stmap_node() -> nuke.Node:
    stmap = create_node("Expression", knobs={"expr0": "x/(width-1)", "expr1": "y/(height-1)", "expr2": "0"})
    stmap.setName("STmap")
    return stmap


def create_crop_with_reformat() -> nuke.Node:
    crop = create_node("Crop")
    crop["box"].setExpression("bbox.x", 0)
    crop["box"].setExpression("bbox.y", 1)
    crop["box"].setExpression("bbox.r", 2)
    crop["box"].setExpression("bbox.t", 3)
    crop["reformat"].setValue(1)
    return crop

def create_crop() -> nuke.Node:
    crop = create_node("Crop")
    crop["box"].setExpression("width", 2)
    crop["box"].setExpression("height", 3)
    return crop

def create_write_dailies(intermediate_name: str = None) -> nuke.Node:
    write = create_node("Write")
    filepath = "[file dirname [value root.name]]/"
    if intermediate_name:
        filepath += f"{intermediate_name}/"
    filepath += "[file rootname [basename [value root.name]]].mov"
    write["file"].setValue(filepath)
    write["colorspace"].setValue("sRGB")
    write["file_type"].setValue("mov")
    write["mov64_codec"].setValue("h264")
    write["mov64_fps"].setExpression("[value root.fps]")
    write["mov64_bitrate"].setValue(20000)
    write["create_directories"].setValue(True)
    write["first"].setValue(FIRST_FRAME)
    write["last"].setValue(LAST_FRAME)
    write["use_limit"].setValue(True)
    return write

def create_write_stmap(intermediate_name: str = None) -> nuke.Node:
    write = create_node("Write")
    filepath = "[file dirname [value root.name]]/"
    if intermediate_name:
        filepath += f"{intermediate_name}/"
    filepath += "stmap/[file rootname [basename [value root.name]]].####.exr"
    write["file"].setValue(filepath)
    write["colorspace"].setValue("linear")
    write["file_type"].setValue("exr")
    write["compression"].setValue("Zip")
    write["create_directories"].setValue(True)
    write["first"].setValue(FIRST_FRAME)
    write["last"].setValue(LAST_FRAME)
    write["use_limit"].setValue(True)
    return write


def create_write_undistort(intermediate_name: str = None) -> nuke.Node:
    write = create_node("Write")
    filepath = "[file dirname [value root.name]]/"
    if intermediate_name:
        filepath += f"{intermediate_name}/"
    filepath += "undistort/[file rootname [basename [value root.name]]].####.exr"
    write["file"].setValue(filepath)
    write["colorspace"].setValue("linear")
    write["file_type"].setValue("exr")
    write["compression"].setValue("DWAA")
    write["create_directories"].setValue(True)
    write["first"].setValue(FIRST_FRAME)
    write["last"].setValue(LAST_FRAME)
    write["use_limit"].setValue(True)
    return write

def create_write_geo(file_type: str, intermediate_name: str = None) -> nuke.Node:
    if not file_type in ["abc", "fbx"]:
        raise ValueError("File type must be abc or fbx.")

    write_geo = create_node("WriteGeo")
    filepath = "[file dirname [value root.name]]/"
    if intermediate_name:
        filepath += f"{intermediate_name}/"
    filepath += f"[file rootname [basename [value root.name]]].{file_type}"
    write_geo["file"].setValue(filepath)
    write_geo["first"].setValue(FIRST_FRAME)
    write_geo["last"].setValue(LAST_FRAME)
    write_geo["use_limit"].setValue(True)
    write_geo["file_type"].setValue(file_type)
    if file_type == "fbx":
        write_geo["animateMeshVertices"].setValue(True)
    return write_geo

def render_dailies(from_node: nuke.Node, intermediate_name: str = None, cleanup_after_render: bool = False) -> None:
    crop = create_crop()
    reformat = create_node("Reformat", knobs={"type": "to_box", "box_width": 2048})
    crop_reformat = create_crop_with_reformat()
    write = create_write_dailies(intermediate_name)
    nodes_to_cleanup = [crop, reformat, crop_reformat, write]

    crop_reformat.setInput(0, from_node)
    reformat.setInput(0, crop_reformat)
    crop.setInput(0, reformat)
    write.setInput(0, crop)

    x_pos, y_pos, space = from_node.xpos(), from_node.ypos(), 1
    crop_reformat.setXYpos(x_pos, y_pos + 100 * space)
    reformat.setXYpos(x_pos, y_pos + 130 * space)
    crop.setXYpos(x_pos, y_pos + 173 * space)
    write.setXYpos(x_pos, y_pos + 205 * space)

    nuke.scriptSave(NUKE_SCRIPT)  # save to crete file

    nuke.render(write)

    if cleanup_after_render:
        for n in nodes_to_cleanup:
            nuke.delete(n)

def render_stmap(from_node: nuke.Node, undistort: nuke.Node, intermediate_name: str = None) -> None:
    stmap = create_stmap_node()
    crop = create_crop()
    undistort_copy = nuke.clone(undistort)
    crop_reformat = create_crop_with_reformat()
    write = create_write_stmap(intermediate_name)
    nodes_to_cleanup = [stmap, crop, undistort_copy, crop_reformat, write]

    stmap.setInput(0, from_node)
    crop.setInput(0, stmap)
    undistort_copy.setInput(0, crop)
    crop_reformat.setInput(0, undistort_copy)
    write.setInput(0, crop_reformat)

    nuke.render(write)

    for n in nodes_to_cleanup:
        nuke.delete(n)

def render_undistort(from_node: nuke.Node, intermediate_name: str = None) -> None:
    crop_reformat = create_crop_with_reformat()
    write = create_write_undistort(intermediate_name)
    nodes_to_cleanup = [crop_reformat, write]

    crop_reformat.setInput(0, from_node)
    write.setInput(0, crop_reformat)

    nuke.render(write)

    for n in nodes_to_cleanup:
        nuke.delete(n)

def render_geo(from_node: nuke.Node, intermediate_name: str = None) -> None:
    write_geo_fbx = create_write_geo("fbx", intermediate_name)
    write_geo_abc = create_write_geo("abc", intermediate_name)

    write_geo_fbx.setInput(0, from_node)
    write_geo_abc.setInput(0, from_node)

    nuke.render(write_geo_fbx)
    nuke.render(write_geo_abc)

    for n in [write_geo_fbx, write_geo_abc]:
        nuke.delete(n)

def shuffle_and_render_nodes(nodes_data) -> None:
    """
    nodes_data = {
        "read_groups": [
            {
                "camera": nuke.Node
                "read": nuke.Node,
                "color_nodes": [nuke.Node, ...],
                "undistort": nuke.Node,
                "stmap": nuke.Node,
                "name": str
            }
        },
        "geo_nodes: [nuke.Node, ...]
        ""
    }
    """
    # scene + geo nodes
    scene = create_node("Scene")
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
        crop = create_crop()
        crop.setInput(0, read)
        y_pos += 86
        crop.setXYpos(x_pos, y_pos)

        # color nodes
        color_nodes = read_group["color_nodes"]
        current_node = None
        previous_node = crop
        for i in range(0, len(color_nodes)):
            current_node = color_nodes[i]

            if i == 0:
                y_pos += 120
            else:
                previous_node = color_nodes[i-1]

            current_node.setInput(0, previous_node)
            current_node.setXYpos(x_pos, y_pos)
            y_pos += 26

        # undistort
        undistort = read_group["undistort"]
        undistort.setInput(0, current_node)
        y_pos += 60
        undistort.setXYpos(x_pos, y_pos)

        # dot + scanline + camera + merge
        y_pos += 120

        dot = create_node("Dot", undistort)
        dot.setXYpos(x_pos + 34, y_pos + 4)

        camera = read_group["camera"]
        camera.setXYpos(x_pos - 400, y_pos - 20)

        scanline = create_node("ScanlineRender", knobs={"motion_vectors_type": "off", "overscan": 500})
        scanline.setInput(0, dot)
        scanline.setInput(1, scene)
        scanline.setInput(2, camera)
        scanline.setXYpos(x_pos - 210, y_pos)

        merge = create_node("Merge2", knobs={"bbox": "B"})
        merge.setInput(0, dot)
        merge.setInput(1, scanline)
        merge.setXYpos(x_pos, y_pos + 80)

        # offset for next read_group
        x_offset += 500

        # render writes
        intermediate_name = read_group["name"] if index else None
        render_stmap(from_node=crop, undistort=undistort, intermediate_name=intermediate_name)
        render_undistort(from_node=undistort, intermediate_name=intermediate_name)
        render_dailies(from_node=merge, intermediate_name=intermediate_name)
        scene.setInput(scene.inputs(), camera)
        render_geo(from_node=scene, intermediate_name=intermediate_name)
        scene.setInput(scene.inputs()-1, None)

def start():

    nuke.scriptOpen(NUKE_SCRIPT)
    nuke.scriptSave(NUKE_SCRIPT)  # save to crete file

    read_groups = []
    for camera_data in JSON_DATA["cameras"]:
        camera = get_camera(camera_data)
        read = import_file_as_read_node(camera_data["source"]["path"])
        softclip = create_soft_clip_node(camera_data)
        grade = create_grade_node(camera_data)
        colorspace_node = create_node("Colorspace", knobs={"colorspace_in": "sRGB"})
        undistort = get_undistort_from_script(camera_data["undistort_script_path"])[0]

        read_groups.append({
            "camera": camera,
            "read": read,
            "color_nodes": [softclip, grade, colorspace_node],
            "undistort": undistort,
            "name": camera_data["name"]
        })

    point_groups = get_point_groups()

    set_root_settings()

    # shuffle nodes
    nodes_data = {
        "read_groups": read_groups,
        "geo_nodes": point_groups
    }
    shuffle_and_render_nodes(nodes_data)

    [nuke.delete(node) for node in nuke.allNodes() if node.Class() == "Viewer"]

    if JSON_DATA["program"] == "3DE4":
        shutil.copy2(JSON_DATA["3de4_project_path"], os.path.dirname(NUKE_SCRIPT))

    nuke.scriptSave(NUKE_SCRIPT)


start()


open_in_explorer(NUKE_SCRIPT)
# TODO: create Cameras with Axis (if Axis needed) +
# TODO: create PointGroups +
# TODO: create Read files +
# TODO: create Undistrot +
# TODO: set Root settings +
# TODO: create STMap +
# TODO: shuffle node + create Write and WriteGeo nodes + render +
#
# TODO: make sure 3DE4 Undistort nodes exists in Nuke
# TODO: checkbox "collect sources"

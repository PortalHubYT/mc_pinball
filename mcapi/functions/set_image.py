import urllib3
import json
import math
from typing import Union
import sys
import os

from PIL import Image

from mcapi.components.BlockCoordinates import BlockCoordinates
from mcapi.components.BlockHandler import BlockHandler
from mcapi.components.Zone import Zone

from mcapi.functions.base_functions import *
from mcapi.functions.set_block import _set_block, set_block

# TODO: Handle image in memory rather than pull
# TODO: Minecart method? -> https://www.youtube.com/watch?v=MEawKJm-t28


def _set_image(
    file: str, coords: BlockCoordinates, orientation: str, player_name: str
) -> dict:

    image = Image.open(file)
    converted_image = image.convert("RGB")

    pixels = list(converted_image.getdata())
    width, height = converted_image.size
    pixels = [pixels[i * width : (i + 1) * width] for i in range(height)]

    instructions = {"list": [], "zone": None}

    palette = get_palette(orientation)

    x = 0

    for line in pixels:
        x += 1
        z = 0

        for pixel in line:

            block = color_picker(pixel, palette)

            if player_name is not None:
                # TODO: Update with the TP method later on
                cmd = f"tp {player_name} {x} {coords.y + 100} {z}"
                instructions["list"].append(cmd)

            new_coords = BlockCoordinates(coords.x + x, coords.y, coords.z + z)

            if orientation in block:
                block = block.replace(f"_{orientation}", "")

                if orientation == "side":
                    block.blockhandler.axis = "x"

                elif orientation == "top":
                    block.blockhandler.axis = "x"

            cmd = _set_block(
                new_coords,
                block,
                BlockHandler("replace"),
            )
            instructions["list"].append(cmd)

            z += 1
    else:
        instructions["zone"] = Zone(
            coords, BlockCoordinates(coords.x + x, coords.y, coords.z + z)
        )

    return instructions


def set_image(
    file: str,
    coords: Union[BlockCoordinates, tuple],
    orientation: str = "side",
    url: bool = False,
    player_name: str = None,
) -> Zone:
    """
    This function takes the path to an image or an URL
    (in which case, url must be passed as True), downloads it,
    and sends back the setblocks instruction to print the image
    in the provided orientation

    Orientation can either be "side", "top", "bottom" depending from where
    you want people to look at the image.

    If a player name is provided, the player will be teleported to make sure the
    printing doesn't happen out of bound (and therefore fail)
    """

    check_output_channel()

    # TODO: Cleanup the file
    if url == True:
        http = urllib3.PoolManager()
        r = http.request("GET", file, preload_content=False)

        filename = "image.jpg"
        with open(filename, "wb") as out:
            while True:
                data = r.read(1024)
                if not data:
                    break
                out.write(data)

        r.release_conn()
        file = filename

    coords = format_arg(coords, BlockCoordinates)

    if orientation not in ["side", "top", "bottom"]:
        raise ValueError(
            f"Orientation must either be side, top or bottom for set_image()"
        )

    instructions = _set_image(file, coords, orientation, player_name)

    for line in instructions["list"]:
        post(line)

    """nest = nest_commands(instructions["lines"])
    post_nest(coords, nest)"""

    return instructions["zone"]


def get_palette(orientation):

    try:
        path = os.path.dirname(os.path.abspath(__file__))
        with open(f"{path}/palette.json") as f:
            palette = json.load(f)

    except FileNotFoundError:
        palette = create_palette()

    return palette[orientation]


def get_closest_color(pixel, block_palette, orientation):

    path = os.path.dirname(os.path.abspath(__file__))
    with open(f"{path}/block_list.json") as f:
        block_list = json.load(f)

    orientations = ["top", "bottom", "front"]
    for index, value in enumerate(orientations):
        if value == orientation:
            orientations.pop(index)

    excluded_block_tags = [
        "shulker",
        "sand",
        "powder",
        "glass",
        "front",
        "coral",
        "dead",
        "trapdoor",
        "chorus",
        "_ore",
    ]

    excluded_blocks = [
        "ice",
    ]

    best_delta = None

    for block in block_palette["averages"]:

        block_name = block["texture"].split("/")[-1]

        if any(other_orientation in block_name for other_orientation in orientations):
            continue

        if f"minecraft:{block_name}" not in list(block_list.keys()):
            continue

        elif any(to_exclude in block_name for to_exclude in excluded_block_tags):
            continue

        elif any(to_exclude == block_name for to_exclude in excluded_blocks):
            continue

        elif block["pixels"] != 256:
            continue

        elif block["stddev_rgb"] == 0.00000:
            continue

        delta = math.sqrt(
            (pixel[0] - block["rgba"][0]) ** 2
            + (pixel[1] - block["rgba"][1]) ** 2
            + (pixel[2] - block["rgba"][2]) ** 2
        )

        if best_delta is None or delta < best_delta:
            best_delta = delta
            best_match = block_name

    return best_match


def color_picker(pixel, palette):

    r = int(pixel[0] / 32)
    g = int(pixel[1] / 32)
    b = int(pixel[2] / 32)

    index = r * 64 + g * 8 + b
    return palette[str(index)]


def print_palette(coords, orientation="side"):
    palette = get_palette(orientation)

    n = 8
    for x in range(n):
        for y in range(n):
            for z in range(n):
                coords = BlockCoordinates(x * 3, y * 3 + 5, z * 3)

                set_block(
                    coords,
                    palette[str(x * 64 + y * 8 + z)],
                )


def create_palette():

    print(
        "It looks like this is the first time you're using set_image() and no pre-existing block palette was found. Please hold on while it's generating!"
    )

    path = os.path.dirname(os.path.abspath(__file__))
    with open(f"{path}/blocks_color.json") as f:
        block_palette = json.load(f)

    palette = {"side": {}, "top": {}, "bottom": {}}

    for orientation in ["side", "top", "bottom"]:

        print(f"-> Generating the palette for the '{orientation}' orientation")

        for i in range(0, 8):
            for j in range(0, 8):
                for k in range(0, 8):

                    block = get_closest_color(
                        (i * 32, j * 32, k * 32), block_palette, orientation
                    )

                    palette[orientation][str(i * 64 + j * 8 + k)] = block

    with open(f"{path}/palette.json", "w+") as f:
        json.dump(palette, f)

    return palette

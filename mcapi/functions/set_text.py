from typing import Union

from mcapi.components.Block import Block
from mcapi.components.BlockCoordinates import BlockCoordinates
from mcapi.components.BlockState import BlockState
from mcapi.components.BlockHandler import BlockHandler
from mcapi.components.Zone import Zone

from mcapi.functions.base_functions import *
from mcapi.functions.set_block import _set_block
from mcapi.functions.set_zone import _set_zone

# TODO: Make clear zone works with scaling
# TODO: orientation
# TODO: vertical text (like japanese)
# TODO: Remove digit skip and encode them
# TODO: handle '\n'
# TODO: flatten scale for every number to usable (but translates to odd numbers)


def _set_text(
    message: str,
    coords: BlockCoordinates,
    palette: list,
    style: str,
    orientation: str,
    replace: BlockHandler,
    scale: int,
    filler: Block,
) -> dict:

    handler = BlockHandler("replace" if replace else "keep")

    offset = 0
    instructions = {"list": [], "zone": None}

    # Can't use enumerate(message) because I don't want
    # to count spaces
    letter_index = 0

    # First we iterate over each letter of the string that
    # was passed
    for index, letter in enumerate(message):

        # If the letter is a space, we skip the loop
        # but add an offset of 2 to the next letter placement
        if letter == " " or letter == "\n":
            offset += 2 + scale
            continue

        try:
            # This condition makes the style "mixed"
            # set the first letter of a string as an uppercase
            if style == "mixed":

                if letter.isupper():
                    letter = letter.lower()
                    representation = letters_dict[letter]["uppercase"]
                else:
                    representation = letters_dict[letter]["lowercase"]

            # Otherwise, it fetches the "representation" (e.g.: 000-421-etc.)
            # of the current letter in the string.
            # The representations are at the bottom of this file.
            else:
                letter = letter.lower()
                representation = letters_dict[letter][style]
        except KeyError:
            offset += 2 + scale
            print("Couldn't find representation for " + letter)
            continue

        # Here we reverse the representation to read it
        # from the bottom left corner to the top right corner
        representation = representation.split("-")
        representation.reverse()

        # This handles when multiple palettes were provided as a list
        # using a modulo based on the length of the palette.
        if len(palette) > 1:
            mod = letter_index % len(palette)
        else:
            mod = 0

        # Then it starts looping through each digit in
        # the representation (e.g.: ["000"], ["414"], etc.)
        y = 0
        for line in representation:

            # After each line it resets the X position to the left
            x = 0 + offset

            for digit in line:

                # This variable stores the computed coordinates at
                # which the current block should be placed
                new_coords = BlockCoordinates(coords.x + x, coords.y + y, coords.z)

                # After which we move the cursor
                x += 1 + scale

                # And finally, this is the part where the block is set
                # depending on whether a scale was specified or not
                if scale == 0:
                    block = fetch_block(digit, orientation, palette[mod], filler)

                    cmd = _set_block(new_coords, block, handler)
                    instructions["list"].append(cmd)

                # In case it was, it creates "zones" instead
                # of placing blocks
                else:
                    zones = construct_zones(new_coords, digit, scale)

                    for zone in zones:

                        # A letter scaled up can be represented by multiple zones
                        # with the slabs for instance, it's half filler(/air),
                        # half solid, so we have to adjust which block
                        # is used per sub zone
                        if zone["filler"] == "air":
                            block = filler
                        elif zone["filler"] == "block":
                            temp_digit = "0" if digit == "0" else "1"
                            block = fetch_block(
                                temp_digit, orientation, palette[mod], filler
                            )

                        cmd = _set_zone(zone["coords"], block, handler)
                        instructions["list"].append(cmd)

            # After a line has been printed, the Y level is increased
            y += 1 + scale

        # This increases the offset after a letter has been printed
        # by computing the length of any 'line' representing
        # the current letter, and adding one block space
        offset += len(representation[0]) * (scale + 1) + 1 * (scale + 1)
        letter_index += 1

    # Y is being re-declared to be used in the return value
    # of the function
    else:
        try:
            y = representation.count("-")
        except UnboundLocalError:
            y = 0
            new_coords = BlockCoordinates(coords.x, coords.y, coords.z)

    new_coords.y += y
    instructions["zone"] = Zone(coords, new_coords)

    # The functions returns the "instructions" dictionary
    # containing all the commands to .post() as well
    # as the zone representing the text that was created
    # for later clean-up
    return instructions


def set_text(
    message: str,
    coords: Union[BlockCoordinates, tuple],
    palette: Union[list, str] = "quartz",
    style: str = "mixed",
    orientation: str = "east",
    replace: bool = True,
    scale: int = 0,
    filler: Union[Block, str] = "air",
) -> Zone:

    """
    Returns a Zone representing the area used by the text
    to be represented

    The given coords should represent the block that is
    lower northwest corner of the structure

    Available styles:
    - smallcaps
    - lowercase
    - uppercase
    - mixed (alternate between lowercase/uppercase by respecting case)

    The availables palettes are listed at the bottom of this file.

    Orientation can be either east(/west) or north(/south)

    Replace is a boolean which defines whether the 'empty' part of
    the text should be replaced by air blocks or left as is

    Scale is the amount of block to "add" to the size of a default block (1)
    e.g: if scale is set to 1, a block will be represented by a 2x2 zone

    Filler represents the block to use in the empty area of the letter
    representation if Replace is set to True
    """

    check_output_channel()

    coords = format_arg(coords, BlockCoordinates)
    filler = format_arg(filler, Block)

    if type(palette) is not list:
        palette = [palette]

    if scale != 0 and (scale % 2) == 0:
        raise ValueError(f"Scale must be an odd number")

    # TODO: Handle this
    """if orientation == "south":
        orientation = "north"
    elif orientation == "east":
        orientation = "west"
    elif orientation != "west" and orientation != "north":
        raise ValueError(f"Orientation must be either north or west for set_text()")"""

    instructions = _set_text(
        message, coords, palette, style, orientation, replace, scale, filler
    )

    for line in instructions["list"]:
        post(line)

    return instructions["zone"]


def construct_zones(coords: BlockCoordinates, digit: str, scale: int) -> list:

    zones = []

    if digit in ["0", "1"]:
        new_coords1 = BlockCoordinates(coords.x, coords.y, coords.z)

        new_coords2 = BlockCoordinates(
            coords.x + scale, coords.y + scale, coords.z + scale
        )

        zones.append({"coords": Zone(new_coords1, new_coords2), "filler": "block"})

    elif digit in ["2", "3"]:

        new_coords1 = BlockCoordinates(coords.x, coords.y + ((scale / 2) + 1), coords.z)
        new_coords2 = BlockCoordinates(
            coords.x + scale, coords.y + scale, coords.z + scale
        )

        zones.append(
            {
                "coords": Zone(new_coords1, new_coords2),
                "filler": "block" if digit == "2" else "air",
            }
        )

        new_coords1 = BlockCoordinates(coords.x, coords.y, coords.z)
        new_coords2 = BlockCoordinates(
            coords.x + scale, coords.y + scale / 2, coords.z + scale
        )

        zones.append(
            {
                "coords": Zone(new_coords1, new_coords2),
                "filler": "block" if digit == "3" else "air",
            }
        )

    elif digit in ["4", "5"]:

        new_coords1 = BlockCoordinates(coords.x, coords.y, coords.z)
        new_coords2 = BlockCoordinates(
            coords.x + scale, coords.y + scale / 2, coords.z + scale
        )

        zones.append(
            {
                "coords": Zone(new_coords1, new_coords2),
                "filler": "block",
            }
        )

        new_coords1 = BlockCoordinates(
            coords.x + ((scale / 2) + 1), coords.y + ((scale / 2) + 1), coords.z
        )
        new_coords2 = BlockCoordinates(
            coords.x + scale, coords.y + scale, coords.z + scale
        )

        zones.append(
            {
                "coords": Zone(new_coords1, new_coords2),
                "filler": "block" if digit == "4" else "air",
            }
        )

        new_coords1 = BlockCoordinates(coords.x, coords.y + ((scale / 2) + 1), coords.z)
        new_coords2 = BlockCoordinates(
            coords.x + scale / 2, coords.y + scale, coords.z + scale
        )

        zones.append(
            {
                "coords": Zone(new_coords1, new_coords2),
                "filler": "block" if digit == "5" else "air",
            }
        )

    elif digit in ["6", "7"]:

        new_coords1 = BlockCoordinates(coords.x, coords.y + ((scale / 2) + 1), coords.z)
        new_coords2 = BlockCoordinates(
            coords.x + scale, coords.y + scale, coords.z + scale
        )

        zones.append(
            {
                "coords": Zone(new_coords1, new_coords2),
                "filler": "block",
            }
        )

        new_coords1 = BlockCoordinates(coords.x + ((scale / 2) + 1), coords.y, coords.z)
        new_coords2 = BlockCoordinates(
            coords.x + scale, coords.y + scale / 2, coords.z + scale
        )

        zones.append(
            {
                "coords": Zone(new_coords1, new_coords2),
                "filler": "block" if digit == "6" else "air",
            }
        )

        new_coords1 = BlockCoordinates(coords.x, coords.y, coords.z)
        new_coords2 = BlockCoordinates(
            coords.x + scale / 2, coords.y + scale / 2, coords.z + scale
        )

        zones.append(
            {
                "coords": Zone(new_coords1, new_coords2),
                "filler": "block" if digit == "7" else "air",
            }
        )

    else:
        zones = []

    return zones


def fetch_block(digit: str, orientation: str, palette: str, filler: Block) -> Block:

    counter_orientation = "west" if orientation == "east" else "south"

    if digit == "1":
        block = block_palette[palette]["block"]

    elif digit == "2":
        block = block_palette[palette]["slab"]
        block.blockstate = BlockState({"type": "top"})

    elif digit == "3":
        block = block_palette[palette]["slab"]
        block.blockstate = BlockState({"type": "bottom"})

    elif digit == "4":
        block = block_palette[palette]["stairs"]
        block.blockstate = BlockState(
            {"facing": orientation, "shape": "straight", "half": "bottom"}
        )

    elif digit == "5":
        block = block_palette[palette]["stairs"]
        block.blockstate = BlockState(
            {"facing": counter_orientation, "shape": "straight", "half": "bottom"}
        )

    elif digit == "6":
        block = block_palette[palette]["stairs"]
        block.blockstate = BlockState(
            {"facing": orientation, "shape": "straight", "half": "top"}
        )

    elif digit == "7":
        block = block_palette[palette]["stairs"]
        block.blockstate = BlockState(
            {"facing": counter_orientation, "shape": "straight", "half": "top"}
        )

    else:
        block = filler

    return block


meta_definition = "custom"

""" Legend: 
  0 = void
  1 = block
  2 = up slab
  3 = low slab
 for the 4 stairs below, they are represented by where their empty quarter of block is
  4 = upper left
  5 = upper right
  6 = bottom left
  7 = bottom right
 each letter is represented by a string of 15 digits,
 separated by a dash for each new column,
 representing a letter in a 3*5 block format

 Source: https://cdn.discordapp.com/attachments/414084871120617472/840083817913385000/ccfe08c.png
"""

letters_dict = {
    "a": {
        "smallcaps": "000-425-131-101-000",
        "uppercase": "425-101-121-101-000",
        "lowercase": "000-425-321-636-000",
    },
    "b": {
        "smallcaps": "000-125-125-137-000",
        "uppercase": "125-135-101-137-000",
        "lowercase": "100-125-101-737-000",
    },
    "c": {
        "smallcaps": "000-425-100-637-000",
        "uppercase": "425-100-100-637-000",
        "lowercase": "000-425-100-637-000",
    },
    "d": {
        "smallcaps": "000-125-101-137-000",
        "uppercase": "125-101-101-137-000",
        "lowercase": "001-421-101-636-000",
    },
    "e": {
        "smallcaps": "000-122-120-133-000",
        "uppercase": "122-130-100-133-000",
        "lowercase": "000-425-122-637-000",
    },
    "f": {
        "smallcaps": "000-122-120-100-000",
        "uppercase": "122-130-100-100-000",
        "lowercase": "425-130-100-100-000",
    },
    "g": {
        "smallcaps": "000-425-103-634-000",
        "uppercase": "425-100-106-637-000",
        "lowercase": "000-424-101-021-637",
    },
    "h": {
        "smallcaps": "000-101-121-101-000",
        "uppercase": "101-131-101-101-000",
        "lowercase": "100-125-101-101-000",
    },
    "i": {
        "smallcaps": "000-212-010-313-000",
        "uppercase": "212-010-010-313-000",
        "lowercase": "020-210-010-313-000",
    },
    "j": {
        "smallcaps": "000-001-001-637-000",
        "uppercase": "001-001-001-637-000",
        "lowercase": "002-021-001-001-637",
    },
    "k": {
        "smallcaps": "000-107-163-101-000",
        "uppercase": "107-140-105-101-000",
        "lowercase": "100-103-160-105-000",
    },
    "l": {
        "smallcaps": "000-100-100-133-000",
        "uppercase": "100-100-100-133-000",
        "lowercase": "100-100-100-637-000",
    },
    "m": {
        "smallcaps": "000-504-111-101-000",
        "uppercase": "504-111-101-101-000",
        "lowercase": "000-555-111-101-000",
    },
    "n": {
        "smallcaps": "000-501-161-106-000",
        "uppercase": "501-151-161-106-000",
        "lowercase": "000-525-101-101-000",
    },
    "o": {
        "smallcaps": "000-425-101-637-000",
        "uppercase": "425-101-101-637-000",
        "lowercase": "000-425-101-637-000",
    },
    "p": {
        "smallcaps": "000-126-137-100-000",
        "uppercase": "125-101-120-100-000",
        "lowercase": "000-525-101-137-100",
    },
    "q": {
        "smallcaps": "000-425-101-645-000",
        "uppercase": "425-101-101-645-000",
        "lowercase": "000-424-101-631-001",
    },
    "r": {
        "smallcaps": "000-125-137-101-000",
        "uppercase": "125-107-121-101-000",
        "lowercase": "000-575-100-100-000",
    },
    "s": {
        "smallcaps": "000-425-263-637-000",
        "uppercase": "425-630-001-637-000",
        "lowercase": "000-425-263-637-000",
    },
    "t": {
        "smallcaps": "000-212-010-010-000",
        "uppercase": "212-010-010-010-000",
        "lowercase": "040-212-010-063-000",
    },
    "u": {
        "smallcaps": "000-101-101-637-000",
        "uppercase": "101-101-101-637-000",
        "lowercase": "000-101-101-636-000",
    },
    "v": {
        "smallcaps": "000-101-607-010-000",
        "uppercase": "101-101-607-010-000",
        "lowercase": "000-101-607-010-000",
    },
    "w": {
        "smallcaps": "000-101-131-706-000",
        "uppercase": "101-101-131-706-000",
        "lowercase": "000-101-131-627-000",
    },
    "x": {
        "smallcaps": "000-637-010-425-000",
        "uppercase": "607-010-010-405-000",
        "lowercase": "000-637-010-425-000",
    },
    "y": {
        "smallcaps": "000-637-010-010-000",
        "uppercase": "101-637-010-010-000",
        "lowercase": "000-101-101-021-637",
    },
    "z": {
        "smallcaps": "000-267-010-453-000",
        "uppercase": "221-047-470-133-000",
        "lowercase": "000-267-010-453-000",
    },
    "*": {
        "smallcaps": "313-425-000-000-000",
        "uppercase": "313-425-000-000-000",
        "lowercase": "313-425-000-000-000",
    },
    "|": {
        "smallcaps": "1-1-1-1-1",
        "uppercase": "1-1-1-1-1",
        "lowercase": "1-1-1-1-1",
    },
    "!": {
        "smallcaps": "010-010-010-030-000",
        "uppercase": "010-010-010-030-000",
        "lowercase": "010-010-010-030-000",
    },
    "?": {
        "smallcaps": "425-007-040-030-000",
        "uppercase": "425-007-040-030-000",
        "lowercase": "425-007-040-030-000",
    },
    "@": {
        "smallcaps": "000-425-554-630-000",
        "uppercase": "000-425-554-630-000",
        "lowercase": "000-425-554-630-000",
    },
    "#": {
        "smallcaps": "000-355-407-662-000",
        "uppercase": "000-355-407-662-000",
        "lowercase": "000-355-407-662-000",
    },
    "&": {
        "smallcaps": "450-670-767-675-000",
        "uppercase": "450-670-767-675-000",
        "lowercase": "450-670-767-675-000",
    },
    "$": {
        "smallcaps": "010-462-615-357-010",
        "uppercase": "010-462-615-357-010",
        "lowercase": "010-462-615-357-010",
    },
    "€": {
        "smallcaps": "033-453-453-650-022",
        "uppercase": "033-453-453-650-022",
        "lowercase": "033-453-453-650-022",
    },
    "£": {
        "smallcaps": "030-425-430-400-763",
        "uppercase": "030-425-430-400-763",
        "lowercase": "030-425-430-400-763",
    },
    "¥": {
        "smallcaps": "607-313-313-010-010",
        "uppercase": "607-313-313-010-010",
        "lowercase": "607-313-313-010-010",
    },
    "~": {
        "smallcaps": "000-000-464-000-000",
        "uppercase": "000-000-464-000-000",
        "lowercase": "000-000-464-000-000",
    },
    "^": {
        "smallcaps": "030-425-000-000-000",
        "uppercase": "030-425-000-000-000",
        "lowercase": "030-425-000-000-000",
    },
    "_": {
        "smallcaps": "000-000-000-333-000",
        "uppercase": "000-000-000-333-000",
        "lowercase": "000-000-000-333-000",
    },
    "+": {
        "smallcaps": "000-010-212-020-000",
        "uppercase": "000-010-212-020-000",
        "lowercase": "000-010-212-020-000",
    },
    "-": {
        "smallcaps": "000-000-222-000-000",
        "uppercase": "000-000-222-000-000",
        "lowercase": "000-000-222-000-000",
    },
    "=": {
        "smallcaps": "000-333-333-000-000",
        "uppercase": "000-333-333-000-000",
        "lowercase": "000-333-333-000-000",
    },
    "/": {
        "smallcaps": "007-040-070-400-000",
        "uppercase": "007-040-070-400-000",
        "lowercase": "007-040-070-400-000",
    },
    "\\": {
        "smallcaps": "600-050-060-005-000",
        "uppercase": "600-050-060-005-000",
        "lowercase": "600-050-060-005-000",
    },
    "%": {
        "smallcaps": "207-040-070-403-000",
        "uppercase": "207-040-070-403-000",
        "lowercase": "207-040-070-403-000",
    },
    "<": {
        "smallcaps": "000-040-400-060-000",
        "uppercase": "000-040-400-060-000",
        "lowercase": "000-040-400-060-000",
    },
    ">": {
        "smallcaps": "000-050-005-070-000",
        "uppercase": "000-050-005-070-000",
        "lowercase": "000-050-005-070-000",
    },
    "(": {
        "smallcaps": "42-10-10-63-00",
        "uppercase": "42-10-10-63-00",
        "lowercase": "42-10-10-63-00",
    },
    ")": {
        "smallcaps": "25-01-01-37-00",
        "uppercase": "25-01-01-37-00",
        "lowercase": "25-01-01-37-00",
    },
    "[": {
        "smallcaps": "12-10-10-13-00",
        "uppercase": "12-10-10-13-00",
        "lowercase": "12-10-10-13-00",
    },
    "]": {
        "smallcaps": "21-01-01-31-00",
        "uppercase": "21-01-01-31-00",
        "lowercase": "21-01-01-31-00",
    },
    "{": {
        "smallcaps": "07-40-60-05-00",
        "uppercase": "07-40-60-05-00",
        "lowercase": "07-40-60-05-00",
    },
    "}": {
        "smallcaps": "60-05-07-40-00",
        "uppercase": "60-05-07-40-00",
        "lowercase": "60-05-07-40-00",
    },
    "`": {
        "smallcaps": "30-25-00-00-00",
        "uppercase": "30-25-00-00-00",
        "lowercase": "30-25-00-00-00",
    },
    ".": {
        "smallcaps": "0-0-0-3-0",
        "uppercase": "0-0-0-3-0",
        "lowercase": "0-0-0-3-0",
    },
    ",": {
        "smallcaps": "0-0-0-3-4",
        "uppercase": "0-0-0-3-4",
        "lowercase": "0-0-0-3-4",
    },
    ":": {
        "smallcaps": "0-3-0-3-0",
        "uppercase": "0-3-0-3-0",
        "lowercase": "0-3-0-3-0",
    },
    ";": {
        "smallcaps": "0-3-0-3-4",
        "uppercase": "0-3-0-3-4",
        "lowercase": "0-3-0-3-4",
    },
    "'": {
        "smallcaps": "5-0-0-0-0",
        "uppercase": "5-0-0-0-0",
        "lowercase": "5-0-0-0-0",
    },
    '"': {
        "smallcaps": "55-00-00-00-00",
        "uppercase": "55-00-00-00-00",
        "lowercase": "55-00-00-00-00",
    },
    "1": {
        "smallcaps": "000-310-010-313-000",
        "uppercase": "310-010-010-313-000",
        "lowercase": "310-010-010-313-000",
    },
    "2": {
        "smallcaps": "000-425-047-413-000",
        "uppercase": "425-007-040-453-000",
        "lowercase": "425-007-040-453-000",
    },
    "3": {
        "smallcaps": "000-425-025-637-000",
        "uppercase": "425-037-001-637-000",
        "lowercase": "425-037-001-637-000",
    },
    "4": {
        "smallcaps": "000-401-131-001-000",
        "uppercase": "401-101-221-001-000",
        "lowercase": "401-101-221-001-000",
    },
    "5": {
        "smallcaps": "000-122-225-637-000",
        "uppercase": "122-130-001-637-000",
        "lowercase": "122-130-001-637-000",
    },
    "6": {
        "smallcaps": "000-425-123-637-000",
        "uppercase": "425-130-101-637-000",
        "lowercase": "425-130-101-637-000",
    },
    "7": {
        "smallcaps": "000-221-047-010-000",
        "uppercase": "221-007-040-010-000",
        "lowercase": "221-007-040-010-000",
    },
    "8": {
        "smallcaps": "000-425-425-637-000",
        "uppercase": "425-637-101-637-000",
        "lowercase": "425-637-101-637-000",
    },
    "9": {
        "smallcaps": "000-425-231-637-000",
        "uppercase": "425-101-021-637-000",
        "lowercase": "425-101-021-637-000",
    },
    "0": {
        "smallcaps": "000-425-141-637-000",
        "uppercase": "425-141-171-637-000",
        "lowercase": "425-141-171-637-000",
    },
    "ç": {
        "smallcaps": "000-425-100-637-040",
        "uppercase": "000-425-100-637-040",
        "lowercase": "000-425-100-637-040",
    },
    "é": {
        "smallcaps": "003-042-000-425-122-637-000",
        "uppercase": "003-042-000-425-122-637-000",
        "lowercase": "003-042-000-425-122-637-000",
    },
    "è": {
        "smallcaps": "300-250-000-425-122-637-000",
        "uppercase": "300-250-000-425-122-637-000",
        "lowercase": "300-250-000-425-122-637-000",
    },
    "î": {
        "smallcaps": "030-425-000-210-010-313-000",
        "uppercase": "030-425-000-210-010-313-000",
        "lowercase": "030-425-000-210-010-313-000",
    },
    "•": {
        "smallcaps": "000-010-000-000-000",
        "uppercase": "000-010-000-000-000",
        "lowercase": "000-010-000-000-000",
    },
    "—": {
        "smallcaps": "000-000-222-000-000",
        "uppercase": "000-000-222-000-000",
        "lowercase": "000-000-222-000-000",
    },
}

block_palette = {
    "oak": {
        "block": Block("oak_planks"),
        "slab": Block("oak_slab"),
        "stairs": Block("oak_stairs"),
    },
    "spruce": {
        "block": Block("spruce_planks"),
        "slab": Block("spruce_slab"),
        "stairs": Block("spruce_stairs"),
    },
    "birch": {
        "block": Block("birch_planks"),
        "slab": Block("birch_slab"),
        "stairs": Block("birch_stairs"),
    },
    "jungle": {
        "block": Block("jungle_planks"),
        "slab": Block("jungle_slab"),
        "stairs": Block("jungle_stairs"),
    },
    "acacia": {
        "block": Block("acacia_planks"),
        "slab": Block("acacia_slab"),
        "stairs": Block("acacia_stairs"),
    },
    "dark_oak": {
        "block": Block("dark_oak_planks"),
        "slab": Block("dark_oak_slab"),
        "stairs": Block("dark_oak_stairs"),
    },
    "crimson": {
        "block": Block("crimson_planks"),
        "slab": Block("crimson_slab"),
        "stairs": Block("crimson_stairs"),
    },
    "warped": {
        "block": Block("warped_planks"),
        "slab": Block("warped_slab"),
        "stairs": Block("warped_stairs"),
    },
    "stone": {
        "block": Block("stone"),
        "slab": Block("stone_slab"),
        "stairs": Block("stone_stairs"),
    },
    "granite": {
        "block": Block("granite"),
        "slab": Block("granite_slab"),
        "stairs": Block("granite_stairs"),
    },
    "polished_granite": {
        "block": Block("polished_granite"),
        "slab": Block("polished_granite_slab"),
        "stairs": Block("polished_granite_stairs"),
    },
    "diorite": {
        "block": Block("diorite"),
        "slab": Block("diorite_slab"),
        "stairs": Block("diorite_stairs"),
    },
    "polished_diorite": {
        "block": Block("polished_diorite"),
        "slab": Block("polished_diorite_slab"),
        "stairs": Block("polished_diorite_stairs"),
    },
    "andesite": {
        "block": Block("andesite"),
        "slab": Block("andesite_slab"),
        "stairs": Block("andesite_stairs"),
    },
    "polished_andesite": {
        "block": Block("polished_andesite"),
        "slab": Block("polished_andesite_slab"),
        "stairs": Block("polished_andesite_stairs"),
    },
    "cobblestone": {
        "block": Block("cobblestone"),
        "slab": Block("cobblestone_slab"),
        "stairs": Block("cobblestone_stairs"),
    },
    "mossy_cobblestone": {
        "block": Block("mossy_cobblestone"),
        "slab": Block("mossy_cobblestone_slab"),
        "stairs": Block("mossy_cobblestone_stairs"),
    },
    "stone_brick": {
        "block": Block("stone_bricks"),
        "slab": Block("stone_brick_slab"),
        "stairs": Block("stone_brick_stairs"),
    },
    "mossy_stone_brick": {
        "block": Block("mossy_stone_bricks"),
        "slab": Block("mossy_stone_brick_slab"),
        "stairs": Block("mossy_stone_brick_stairs"),
    },
    "brick": {
        "block": Block("bricks"),
        "slab": Block("brick_slab"),
        "stairs": Block("brick_stairs"),
    },
    "end_stone_brick": {
        "block": Block("end_stone_bricks"),
        "slab": Block("end_stone_brick_slab"),
        "stairs": Block("end_stone_brick_stairs"),
    },
    "nether_brick": {
        "block": Block("nether_bricks"),
        "slab": Block("nether_brick_slab"),
        "stairs": Block("nether_brick_stairs"),
    },
    "red_nether_brick": {
        "block": Block("red_nether_bricks"),
        "slab": Block("red_nether_brick_slab"),
        "stairs": Block("red_nether_brick_stairs"),
    },
    "sandstone": {
        "block": Block("sandstone"),
        "slab": Block("sandstone_slab"),
        "stairs": Block("sandstone_stairs"),
    },
    "smooth_sandstone": {
        "block": Block("smooth_sandstone"),
        "slab": Block("smooth_sandstone_slab"),
        "stairs": Block("smooth_sandstone_stairs"),
    },
    "red_sandstone": {
        "block": Block("red_sandstone"),
        "slab": Block("red_sandstone_slab"),
        "stairs": Block("red_sandstone_stairs"),
    },
    "smooth_red_sandstone": {
        "block": Block("smooth_red_sandstone"),
        "slab": Block("smooth_red_sandstone_slab"),
        "stairs": Block("smooth_red_sandstone_stairs"),
    },
    "quartz": {
        "block": Block("quartz_block"),
        "slab": Block("quartz_slab"),
        "stairs": Block("quartz_stairs"),
    },
    "smooth_quartz": {
        "block": Block("smooth_quartz"),
        "slab": Block("smooth_quartz_slab"),
        "stairs": Block("smooth_quartz_stairs"),
    },
    "purpur": {
        "block": Block("purpur_block"),
        "slab": Block("purpur_slab"),
        "stairs": Block("purpur_stairs"),
    },
    "prismarine": {
        "block": Block("prismarine"),
        "slab": Block("prismarine_slab"),
        "stairs": Block("prismarine_stairs"),
    },
    "prismarine_brick": {
        "block": Block("prismarine_brick"),
        "slab": Block("prismarine_brick_slab"),
        "stairs": Block("prismarine_brick_stairs"),
    },
    "dark_prismarine": {
        "block": Block("dark_prismarine"),
        "slab": Block("dark_prismarine_slab"),
        "stairs": Block("dark_prismarine_stairs"),
    },
    "blackstone": {
        "block": Block("blackstone"),
        "slab": Block("blackstone_slab"),
        "stairs": Block("blackstone_stairs"),
    },
    "polished_blackstone": {
        "block": Block("polished_blackstone"),
        "slab": Block("polished_blackstone_slab"),
        "stairs": Block("polished_blackstone_stairs"),
    },
    "polished_blackstone_brick": {
        "block": Block("polished_blackstone_bricks"),
        "slab": Block("polished_blackstone_brick_slab"),
        "stairs": Block("polished_blackstone_brick_stairs"),
    },
}

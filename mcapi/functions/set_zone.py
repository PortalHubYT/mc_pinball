from typing import Union

from mcapi.components.Block import Block
from mcapi.components.Zone import Zone
from mcapi.components.BlockHandler import BlockHandler

from mcapi.functions.base_functions import *


def _set_zone(
    zone: Zone, block: Block, handler: BlockHandler, filter: Union[Block, None] = None
) -> dict:

    instructions = {"list": []}

    if str(handler) == "replace" and filter:
        handler = str(handler) + " " + str(filter)

    instructions["list"].append(f"fill {zone} {block} {handler}")

    return instructions


def set_zone(
    zone: Union[Zone, list],
    block: Union[Block, str],
    handler: Union[BlockHandler, str] = "replace",
    filter: Union[Block, str] = "",
) -> str:
    """
    Returns a bool that is set to True
    if no message was sent back by the game or the
    message itself if there was an issue

    Available handlers:
        'replace' — The old block drops neither itself nor any contents. Plays no sound.
        'destroy' — The old block drops both itself and its contents (as if destroyed by a player). Plays the appropriate block breaking noise.
        'keep' — Only air blocks are changed (non-air blocks are unchanged).
        'hollow' - Replaces only the blocks on the outer edge of the fill region with the
        specified block. Inner blocks are changed to air, dropping their contents as entities
        but not themselves. If the fill region has no inner blocks (because it is smaller than
        three blocks in at least one dimension), acts like 'replace'.
        'outline' - Replaces only the blocks on the outer edge of the fill region with the
        specified block. Inner blocks are not affected. If the fill region has no inner blocks
        (because it is smaller than three blocks in at least one dimension), acts like 'replace'.

    Defaults to 'replace'
    """

    check_output_channel()

    zone = format_arg(zone, Zone)
    block = format_arg(block, Block)
    handler = format_arg(handler, BlockHandler)

    if filter != "":
        filter = format_arg(filter, Block)

    instructions = _set_zone(zone, block, handler, filter)

    for line in instructions["list"]:
        status = post(line)

    return default_check(status)

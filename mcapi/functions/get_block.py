from typing import Union

from mcapi.components.Block import Block
from mcapi.components.BlockState import BlockState
from mcapi.components.BlockCoordinates import BlockCoordinates
from mcapi.components.BlockHandler import BlockHandler

from mcapi.functions.base_functions import *


def _get_block(coords: BlockCoordinates, block: Block, handler: BlockHandler) -> dict:
    return f"setblock {coords} {block} {handler}"


def get_block(
    coords: Union[BlockCoordinates, tuple],
) -> Block:

    """
    Returns a Block
    Available handlers:
        'replace' — The old block drops neither itself nor any contents. Plays no sound.
        'destroy' — The old block drops both itself and its contents (as if destroyed by a player). Plays the appropriate block breaking noise.
        'keep' — Only air blocks are changed (non-air blocks are unchanged).

    Defaults to 'replace'
    """

    check_output_channel()

    coords = format_arg(coords, BlockCoordinates)

    instructions = _get_block(coords)

    for line in instructions["list"]:
        post(line)

    return


meta_definition = "custom"

"""
1. Check if block above is air/or +256
2. If not -> store the block type
3. Spawn the arrow as close as needed
3bis. If the arrow didn't hit anything, bruteforce check the block, otherwise:
4. Check the arrow inBlockState nbt data
5. Put the block back
"""

import unittest

from mcapi.components.Block import Block
from mcapi.components.Coordinates import Coordinates
from mcapi.components.BlockHandler import BlockHandler
from mcapi.components.BlockState import BlockState


class TestBlockHandler(unittest.TestCase):
    def test_handler_real_case(self):
        command = f'setblock {Coordinates(0, 0, 0)} {Block("bedrock")} {BlockHandler("destroy")}'

        diff = str(command)
        test = "setblock 0 0 0 minecraft:bedrock destroy"
        self.assertEqual(diff, test)

    def test_fill_with_blockstate(self):
        pos1 = Coordinates(0, 4, 0)
        pos2 = Coordinates(10, 4, 10)
        bs = BlockState({"facing": "north", "half": "top"})
        block = Block("oak_stairs", blockstate=bs)

        command = f"fill {pos1} {pos2} {block}"

        diff = str(command)
        expected = "fill 0 4 0 10 4 10 minecraft:oak_stairs[facing=north,half=top]"
        self.assertEqual(diff, expected)

import unittest

from mcapi.components.Block import Block
from mcapi.components.BlockState import BlockState
from mcapi.components.BlockCoordinates import BlockCoordinates
from mcapi.components.BlockHandler import BlockHandler

from mcapi.functions.set_block import set_block, _set_block


class TestBlock(unittest.TestCase):
    def test_set_block(self):
        coords = BlockCoordinates(0, 0, 0)
        block = Block("bedrock")
        handler = BlockHandler("destroy")

        diff = _set_block(coords, block, handler)
        test = "setblock 0 0 0 minecraft:bedrock destroy"
        self.assertEqual(diff, test)


if __name__ == "__main__":
    unittest.main()

import unittest

from mcapi.components.Block import Block
from mcapi.components.BlockState import BlockState
from mcapi.components.NBT import NBT


class TestBlock(unittest.TestCase):
    def test_block_bedrock(self):
        block = Block("bedrock")

        diff = str(block)
        test = "minecraft:bedrock"
        self.assertEqual(diff, test)

    def test_block_namespace(self):
        block = Block("mod:op_block")

        diff = str(block)
        test = "mod:op_block"
        self.assertEqual(diff, test)

    def test_block_simple_blockstate(self):
        block = Block("bedrock")
        block.blockstate = BlockState({"facing": "north"})

        diff = str(block)
        test = "minecraft:bedrock[facing=north]"
        self.assertEqual(diff, test)

    def test_block_double_blockstate(self):
        block = Block("bedrock")
        block.blockstate = BlockState({"facing": "north", "half": "top"})

        diff = str(block)
        test = "minecraft:bedrock[facing=north,half=top]"
        self.assertEqual(diff, test)

    def test_block_simple_nbt(self):
        block = Block("bedrock")
        block.nbt = NBT({"Fire": 4})

        diff = str(block)
        test = "minecraft:bedrock{Fire:4}"
        self.assertEqual(diff, test)

    def test_block_double_nbt(self):
        block = Block("bedrock")
        block.nbt = NBT({"Fire": 4, "Air": 0})

        diff = str(block)
        test = "minecraft:bedrock{Air:0,Fire:4}"
        self.assertEqual(diff, test)

    def test_block_mixed(self):
        block = Block("bedrock")
        block.nbt = NBT({"Fire": 4, "Air": 0})
        block.blockstate = BlockState({"facing": "north", "half": "top"})

        diff = str(block)
        test = "minecraft:bedrock[facing=north,half=top]{Air:0,Fire:4}"
        self.assertEqual(diff, test)

    def test_empty(self):
        with self.assertRaises(ValueError):
            Block("")


if __name__ == "__main__":
    unittest.main()

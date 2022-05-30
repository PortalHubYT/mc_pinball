import unittest

from mcapi.components.Block import Block
from mcapi.components.Zone import Zone
from mcapi.components.BlockCoordinates import BlockCoordinates
from mcapi.components.BlockHandler import BlockHandler

from mcapi.functions.set_zone import _set_zone


class TestBlock(unittest.TestCase):
    def test_set_zone(self):
        coords = BlockCoordinates(0, 0, 0)
        coords2 = BlockCoordinates(10, 10, 10)
        zone = Zone(coords, coords2)
        block = Block("bedrock")
        filter = Block("sponge")
        handler = BlockHandler("hollow")

        diff = _set_zone(zone, block, handler, filter)
        test = "fill 0 0 0 10 10 10 minecraft:bedrock hollow"
        self.assertEqual(diff, test)

    def test_set_zone_replace(self):
        coords = BlockCoordinates(0, 0, 0)
        coords2 = BlockCoordinates(10, 10, 10)
        zone = Zone(coords, coords2)
        block = Block("bedrock")
        filter = Block("sponge")
        handler = BlockHandler("replace")

        diff = _set_zone(zone, block, handler, filter)
        test = "fill 0 0 0 10 10 10 minecraft:bedrock replace minecraft:sponge"
        self.assertEqual(diff, test)

    def test_set_zone_no_handler(self):
        coords = BlockCoordinates(0, 0, 0)
        coords2 = BlockCoordinates(10, 10, 10)
        zone = Zone(coords, coords2)
        block = Block("bedrock")
        handler = BlockHandler()

        diff = _set_zone(zone, block, handler)
        test = "fill 0 0 0 10 10 10 minecraft:bedrock replace"
        self.assertEqual(diff, test)


if __name__ == "__main__":
    unittest.main()

import unittest

from mcapi.components.BlockCoordinates import BlockCoordinates
from mcapi.components.Zone import Zone, ZoneWrongCoordsType


class TestCoordinates(unittest.TestCase):
    def test_zone_with_blockcoords(self):
        coords1 = BlockCoordinates(0, 0, 0)
        coords2 = BlockCoordinates(10, 10, 10)
        zone = Zone(coords1, coords2)

        diff = str(zone)
        test = "0 0 0 10 10 10"
        self.assertEqual(diff, test)

    def test_zone_with_tuple(self):
        coords1 = (0, 0, 0)
        coords2 = (10, 10, 10)
        zone = Zone(coords1, coords2)

        diff = str(zone)
        test = "0 0 0 10 10 10"
        self.assertEqual(diff, test)

    def test_zone_mixed(self):
        coords1 = (0, 0, 0)
        coords2 = BlockCoordinates(10, 10, 10)
        zone = Zone(coords1, coords2)

        diff = str(zone)
        test = "0 0 0 10 10 10"
        self.assertEqual(diff, test)

    def test_zone_wrong_args(self):
        zone = Zone("hello", 1)
        with self.assertRaises(ZoneWrongCoordsType):
            str(zone)


if __name__ == "__main__":
    unittest.main()

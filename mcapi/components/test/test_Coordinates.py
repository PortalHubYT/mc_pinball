import unittest

from mcapi.components.Coordinates import Coordinates, WrongCaretNotation


class TestCoordinates(unittest.TestCase):
    def test_coords_zeros(self):
        coords = Coordinates(0, 0, 0)

        diff = str(coords)
        test = "0 0 0"
        self.assertEqual(diff, test)

    def test_coords_tilde(self):
        coords = Coordinates("~", "~", "~")

        diff = str(coords)
        test = "~ ~ ~"
        self.assertEqual(diff, test)

    def test_coords_tilde_mixed(self):
        coords = Coordinates("~5", 0, "~-10")

        diff = str(coords)
        test = "~5 0 ~-10"
        self.assertEqual(diff, test)

    def test_coords_caret(self):
        coords = Coordinates("^", "^", "^")

        diff = str(coords)
        test = "^ ^ ^"
        self.assertEqual(diff, test)

    def test_coords_caret_mixed(self):
        coords = Coordinates("^5", "^-10", "^")

        diff = str(coords)
        test = "^5 ^-10 ^"
        self.assertEqual(diff, test)

    def test_coords_caret_wrong(self):
        coords = Coordinates(5, "^", "^")

        with self.assertRaises(WrongCaretNotation):
            str(coords)

    def test_coords_floats(self):
        coords = Coordinates(1.5, "~0.1", 1)

        diff = str(coords)
        test = "1.5 ~0.1 1"
        self.assertEqual(diff, test)


if __name__ == "__main__":
    unittest.main()

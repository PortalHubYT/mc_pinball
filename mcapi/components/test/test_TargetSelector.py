import unittest

from mcapi.components.TargetSelector import TargetSelector
from mcapi.components.TargetSelector import (
    IncorrectTargetSelectorIdentifier,
    IncorrectTargetSelectorArgumentsType,
    InvalidTargetSelectorArgumentKey,
)


class TestBlock(unittest.TestCase):
    def test_targetselector_p_option(self):
        ts = TargetSelector("p")

        diff = str(ts)
        test = "@p[]"
        self.assertEqual(diff, test)

    def test_targetselector_a_option(self):
        ts = TargetSelector("a")

        diff = str(ts)
        test = "@a[]"
        self.assertEqual(diff, test)

    def test_targetselector_r_option(self):
        ts = TargetSelector("r")

        diff = str(ts)
        test = "@r[]"
        self.assertEqual(diff, test)

    def test_targetselector_s_option(self):
        ts = TargetSelector("s")

        diff = str(ts)
        test = "@s[]"
        self.assertEqual(diff, test)

    def test_targetselector_e_option(self):
        ts = TargetSelector("e")

        diff = str(ts)
        test = "@e[]"
        self.assertEqual(diff, test)

    def test_targetselector_invalid_option(self):
        with self.assertRaises(IncorrectTargetSelectorIdentifier):
            TargetSelector("f")

    def test_targetselector_with_no_arguments(self):
        ts = TargetSelector("p", {})

        diff = str(ts)
        test = "@p[]"
        self.assertEqual(diff, test)

    def test_targetselector_with_argument(self):
        ts = TargetSelector("p", {"team": "french"})

        diff = str(ts)
        test = "@p[team=french]"
        self.assertEqual(diff, test)

    def test_targetselector_with_arguments(self):
        ts = TargetSelector("p", {"team": "french", "tag": "baguette"})

        diff = str(ts)
        test = "@p[team=french,tag=baguette]"
        self.assertEqual(diff, test)

    def test_targetselector_with_arguments_listed(self):
        ts = TargetSelector("p", {"team": "french", "tag": ["baguette", "farine"]})

        diff = str(ts)
        test = "@p[team=french,tag=baguette,tag=farine]"
        self.assertEqual(diff, test)

    def test_targetselector_with_invalid_arguments(self):
        with self.assertRaises(InvalidTargetSelectorArgumentKey):
            str(TargetSelector("p", {"totem": 5, "tag": "baguette"}))

    def test_targetselector_with_invalid_argument_type(self):
        with self.assertRaises(IncorrectTargetSelectorArgumentsType):
            str(TargetSelector("p", ["totem", "tag", 5]))


if __name__ == "__main__":
    unittest.main()

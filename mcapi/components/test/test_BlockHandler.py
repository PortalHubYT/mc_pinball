import unittest

from mcapi.components.BlockHandler import BlockHandler, BlockHandlerWrongType
from mcapi.components.Block import Block


class TestBlockHandler(unittest.TestCase):
    def test_handler_destroy(self):
        bh = BlockHandler("destroy")

        diff = str(bh)
        test = "destroy"
        self.assertEqual(diff, test)

    def test_handler_replace(self):
        bh = BlockHandler("replace")

        diff = str(bh)
        test = "replace"
        self.assertEqual(diff, test)

    def test_handler_keep(self):
        bh = BlockHandler("keep")

        diff = str(bh)
        test = "keep"
        self.assertEqual(diff, test)

    def test_handler_hollow(self):
        bh = BlockHandler("hollow")

        diff = str(bh)
        test = "hollow"
        self.assertEqual(diff, test)

    def test_handler_outline(self):
        bh = BlockHandler("outline")

        diff = str(bh)
        test = "outline"
        self.assertEqual(diff, test)

    def test_handler_default(self):
        bh = BlockHandler()

        diff = str(bh)
        test = "replace"
        self.assertEqual(diff, test)

    def test_abritrary_handler(self):
        bh = BlockHandler("imaginary")

        with self.assertRaises(BlockHandlerWrongType):
            str(bh)

    def test_wrong_handler_type(self):
        bh = BlockHandler(1)

        with self.assertRaises(BlockHandlerWrongType):
            str(bh)


if __name__ == "__main__":
    unittest.main()

import unittest

from mcapi.components.Entity import Entity, IncorrectEntityDescriptorType
from mcapi.components.TargetSelector import TargetSelector


class TestBlock(unittest.TestCase):
    def test_entity_player_name(self):
        entity = Entity("Steve")

        diff = str(entity)
        test = "Steve"
        self.assertEqual(diff, test)

    def test_entity_UUID(self):
        entity = Entity("dd12be42-52a9-4a91-a8a1-11c01849e498")

        diff = str(entity)
        test = "dd12be42-52a9-4a91-a8a1-11c01849e498"
        self.assertEqual(diff, test)

    def test_entity_TargetSelector(self):
        ts = TargetSelector("p", {"tag": "cat"})
        entity = Entity(ts)

        diff = str(entity)
        test = "@p[tag=cat]"
        self.assertEqual(diff, test)

    def test_entity_invalid_descriptor(self):
        with self.assertRaises(IncorrectEntityDescriptorType):
            Entity(["apple", "dog"])

    def test_entity_incorrect_descriptor(self):
        with self.assertRaises(ValueError):
            Entity("")


if __name__ == "__main__":
    unittest.main()

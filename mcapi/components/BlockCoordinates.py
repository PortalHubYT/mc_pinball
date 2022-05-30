import math

from .Coordinates import Coordinates


class BlockCoordinates(Coordinates):
    """
    The position of a block is actually the coordinates of the point at the lower northwest corner
    of the block, that is, the integer coordinates obtained by rounding down the coordinates
    inside the block.

    In Minecraft, decimal coordinates usually needs to be converted into integer coordinates by rounding
    down, which is called the block position of the coordinate.
    """

    def floor(self, coord):
        # Below is the worst bricolage in the history of bricolage
        # '^1.1' becomes '^1'

        if isinstance(coord, str) and "." in coord:

            if coord.startswith("^"):
                value = coord.split("^")[1]
                value = float(value)
                value = math.floor(value)
                coord = "^" + str(value)

            elif coord.startswith("~"):
                value = coord.split("~")[1]
                value = float(value)
                value = math.floor(value)
                coord = "~" + str(value)

            else:
                coord = math.floor(float(coord))

        elif isinstance(coord, float):
            coord = math.floor(coord)

        return coord

    def __str__(self):

        self.check_carets()

        self.x = self.floor(self.x)
        self.y = self.floor(self.y)
        self.z = self.floor(self.z)

        return f"{self.x} {self.y} {self.z}"

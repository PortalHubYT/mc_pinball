from typing import Union

from .BlockCoordinates import BlockCoordinates


class Zone:
    """
    Custom component that is a set of two BlockCoordinates(), representing
    a rectangular area
    """

    def __init__(
        self, pos1: Union[BlockCoordinates, tuple], pos2: Union[BlockCoordinates, tuple]
    ):

        if isinstance(pos1, tuple):
            self.pos1 = BlockCoordinates(*pos1)
        else:
            self.pos1 = pos1

        if isinstance(pos2, tuple):
            self.pos2 = BlockCoordinates(*pos2)
        else:
            self.pos2 = pos2

    def __str__(self):
        if not isinstance(self.pos1, BlockCoordinates) or not isinstance(
            self.pos2, BlockCoordinates
        ):
            raise ZoneWrongCoordsType(
                "a Zone requires to be provided a set of two BlockCoordinates instances as pos1 and pos2"
            )

        return f"{self.pos1} {self.pos2}"


class ZoneWrongCoordsType(Exception):
    pass

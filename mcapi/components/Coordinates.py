from typing import Union


class Coordinates:
    def __init__(
        self,
        x: Union[int, float, str],
        y: Union[int, float, str],
        z: Union[int, float, str],
    ):

        self.x = x
        self.y = y
        self.z = z
        self.set = (self.x, self.y, self.z)

    def check_carets(self):
        coords = [self.x, self.y, self.z]

        if any(str(coord).startswith("^") for coord in coords):
            if not all(str(coord).startswith("^") for coord in coords):
                raise WrongCaretNotation(
                    "When using caret notation, every coordinates must start with a caret"
                )

    def __str__(self):
        self.check_carets()

        return f"{self.x} {self.y} {self.z}"


class WrongCaretNotation(Exception):
    pass

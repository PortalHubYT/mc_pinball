import re


class NBT:
    """
    Every arguments or attributes given to NBT must be written
    using the correct case provided by Minecraft.

    E.G.:
        -> AbsorptionAmount
        -> CustomName
        -> Fire

    If the case is not respected, the tags won't be applied.
    """

    def __init__(self, compound: dict = None):

        if isinstance(compound, dict):
            for key in compound:
                setattr(self, key, compound[key])

    def flatten(self, arg):
        if isinstance(arg, dict):
            return str(NBT(arg))

        elif isinstance(arg, str):  # see test_NBT_with_args in test_NBT.py
            if '"' in arg:
                return f"'{arg}'"
            else:
                return f'"{arg}"'

        elif isinstance(arg, float):
            return f"{arg}d"

        else:
            return str(arg)

    def __str__(self):

        buff = ""

        for key in dir(self):
            if key.startswith("__"):
                continue
            elif key == "flatten":
                continue

            value = getattr(self, key)
            value = self.flatten(value)

            buff += f"{key}:{value},"

        if buff != "":
            buff = buff[:-1]
            return f"{{{buff}}}"
        else:
            return ""

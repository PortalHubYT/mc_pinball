class BlockState:
    def __init__(self, properties: dict = None):

        if isinstance(properties, dict):
            for key in properties:
                setattr(self, key, properties[key])

        elif properties is not None:
            raise ValueError("BlockState arg must be a dictionnary")

    def flatten(self, arg):

        if isinstance(arg, bool):
            if arg == True:
                return "true"
            else:
                return "false"

        elif isinstance(arg, int):
            return str(arg)

        elif isinstance(arg, str):
            return arg

        else:
            raise UnexpectedBlockStatePropertyValueType(
                f"The type of: [{arg}] is [{type(arg)}] and is not valid for blockstate. The value must either be an int, a boolean or a string"
            )

    def __str__(self):

        buff = ""

        for key in dir(self):
            if key.startswith("__"):
                continue
            elif key == "flatten":
                continue

            value = getattr(self, key)
            value = self.flatten(value)
            buff += f"{key}={value},"

        if buff != "":
            buff = buff[:-1]
            return f"[{buff}]"
        else:
            return ""


class UnexpectedBlockStatePropertyValueType(Exception):
    pass

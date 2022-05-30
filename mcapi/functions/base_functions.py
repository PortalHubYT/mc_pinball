from mcapi.components.BlockCoordinates import BlockCoordinates
from mcapi.server.singleton import singleton

__all__ = [
    "check_output_channel",
    "post",
    "default_check",
    "execute_check",
    "unexpected_status",
    "format_arg",
    "nest_commands",
    "post_nest",
]


def check_output_channel():
    if singleton.check_status():
        return singleton
    else:
        raise NoOutputChannelProvided(f"No output channel was initialized in the code")


def post(cmd: str):
    return singleton.post(cmd)


def post_nest(coords: BlockCoordinates, nest: list):
    for index, egg in enumerate(nest):
        cmd = f'/setblock {coords.x} {coords.y + index + 2} {coords.z} command_block{{Command:"{egg}",auto:1b,conditionMet:1b}} replace'
        cmd += "\n"
        print(cmd)
        singleton.post(cmd)


def nesting_process(instructions):

    nested_cmd = f"summon falling_block ~ ~1 ~"

    nested_cmd += " {Time:1,BlockState:{Name:redstone_block},Passengers:[{id:falling_block,Passengers:[{id:falling_block,Time:1,BlockState:{Name:activator_rail},Passengers:["

    for line in instructions:
        nested_cmd += f'{{id:command_block_minecart,Command:"{line}"}},'

    nested_cmd += "{id:command_block_minecart,Command:'setblock ~ ~1 ~ command_block{auto:1,Command:\"fill ~ ~ ~ ~ ~-3 ~ air\"}'},"
    nested_cmd += "{id:command_block_minecart,Command:'kill @e[distance=..1]'}]}]}]}"

    return nested_cmd


def nest_commands(instructions):

    nest = []

    pckg = []
    total_length = 0
    while len(instructions):
        print(len(instructions))
        if total_length < 1600:
            total_length += len(instructions[0])
            pckg.append(instructions[0])
            instructions.pop(0)
        else:
            nest.append(nesting_process(pckg))
            pckg = []
            total_length = 0

    return nest


def default_check(response):
    if response == "":
        return True
    else:
        return response


def execute_check(response):
    if response == "Test passed":
        return True
    elif response == "Test failed":
        return False
    else:
        return response


def unexpected_status(file_name, status):
    raise UnexpectedReturn(
        f'The say command in {file_name.split("/")[-1]} didn\'t properly function and returned: "{status}"'
    )


def format_arg(argument, component):
    if isinstance(argument, component):
        return argument

    if isinstance(argument, str):
        return component(argument)
    elif isinstance(argument, tuple):
        return component(*argument)
    elif isinstance(argument, list):
        return component(*argument)
    else:
        raise InvalidArgumentType(
            f'Invalid argument type, could not parse "{argument}" as a valid component.'
        )


class InvalidArgumentType(Exception):
    pass


class UnexpectedReturn(Exception):
    pass


class NoOutputChannelProvided(Exception):
    pass

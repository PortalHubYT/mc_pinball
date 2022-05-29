import asyncio
from os import environ
import txaio

txaio.use_asyncio()
from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner
from autobahn.wamp.exception import ApplicationError

import types
import readline
import re
import gamestate


class Console(ApplicationSession):
    async def onJoin(self, details):

        self.gamestate = await gamestate.create(self)

        async def board_peg_line(*args):
            try:
                y = int(args[0])
                spacing = int(args[1])
            except Exception:
                print("""Requires 2 arguments: y and spacing""")

            await self.call("arena.place_peg_line", int(y), int(spacing))

        async def board_peg_spawn(*args):
            try:
                x = int(args[0])
                y = int(args[1])
            except Exception:
                print("""Requires 2 arguments: x and y""")
                return

            await self.call("arena.place_peg", int(x), int(y))

        async def board_peg_remove(*args):
            try:
                if args[0] == "line":
                    y = int(args[1])
                    load = (y,)
                    call = "arena.remove_peg_line"
                else:
                    x = int(args[0])
                    y = int(args[1])
                    load = (x, y)
                    call = "arena.remove_peg"

            except Exception as e:
                print("""Requires 2 arguments: x and y""")
                return

            await self.call(call, *load)

        async def board_query(*args):
            try:
                key = args[0]
            except Exception:
                print("""Requires 1 argument: key""")
                return
            try:
                ret = self.gamestate[key]
                print(f"{key} = {ret}")
            except ApplicationError:
                print("Key doesn't exist")
                return

        async def board_set(*args):
            try:
                key = args[0]
            except Exception:
                print("""Requires 1 argument: key""")
                return

            # Order is important because second matches for first but not otherwise
            # Seeks "key=x"
            rgxs = [
                r"^(.*)(-=)(.*)$",
                r"^(.*)(\+=)(.*)$",
                r"^(.*)(=)(.*)$",
            ]

            for rgx in rgxs:
                res = re.search(rgx, key)
                if res != None:
                    key = res.group(1)
                    value = res.group(3)
                    modificator = res.group(2)

                    try:
                        value = int(value)
                        if modificator == "-=":
                            value = -int(value)
                        elif modificator == "+=":
                            value = int(value)
                    except ValueError:
                        pass

                    if key not in self.gamestate._state.__dir__():
                        print(f"{key} is not a valid key in the board environment")
                        return

                    if modificator == "=":
                        self.gamestate[key] = value
                    else:
                        self.gamestate[key] = self.gamestate[key] + value

                    break

        architecture = {
            "board": {
                "peg": {
                    "line": board_peg_line,
                    "spawn": board_peg_spawn,
                    "remove": board_peg_remove,
                },
                "construct": None,
                "deconstruct": None,
                "query": board_query,
                "set": board_set,
            }
        }

        cursor = []
        link = architecture.copy()
        previous_link = None
        end_of_branch = False
        still_on_end_of_brench = False
        while True:
            try:

                def path():
                    return ".".join(cursor)

                pwd = path().replace(".", " -> ") if cursor != [] else "root"
                cmd = input(f"[{pwd}]-> ")
                if cmd == "":
                    continue

                if cmd == "ls":

                    if end_of_branch:
                        print("No child directory")
                        continue

                    dirs = []
                    for key in link:
                        if type(link[key]) is dict:
                            dirs.append(key)

                    print()
                    print("\t\t".join(dirs))
                    print()
                    continue

                elif cmd.startswith("cd "):
                    arg = cmd.split(" ")[1]

                    if arg == "..":
                        if len(cursor) == 1:
                            link = architecture
                        elif cursor != []:
                            link = previous_link[cursor[-2]]
                        elif cursor == []:
                            continue

                        end_of_branch = False
                        still_on_end_of_brench = False
                        cursor.pop()

                    elif arg in link:
                        found = None
                        for key in link:
                            if type(link[key]) is dict:
                                for item in link[key]:
                                    if type(item) is dict:
                                        found = True

                        if found or len(cursor) == 0:
                            previous_link = link
                            link = link[arg]
                            end_of_branch = False
                        elif not found:
                            end_of_branch = True

                        if arg not in cursor:
                            cursor.append(arg)

                    continue

                elif cmd == "help":
                    print(
                        """
                    ls - list current directory
                    cd [directory] - change directory
                    cmd - list commands in directory
                    help - show this help
                    """
                    )
                    continue

                elif cmd == "cmd":

                    cmds = []

                    if end_of_branch and not still_on_end_of_brench:
                        link = link[cursor[-1]]
                        still_on_end_of_brench = True

                    for key in link:
                        if (
                            isinstance(link[key], types.FunctionType)
                            or link[key] is None
                        ):
                            cmds.append(key)

                    if cmds == []:
                        print("No commands in this directory")
                        continue

                    print()
                    print("\t".join(cmds))
                    print()
                    continue

                else:

                    if end_of_branch and not still_on_end_of_brench:
                        link = link[cursor[-1]]
                        still_on_end_of_brench = True

                    query = cmd.split(" ")[0]
                    if query in link:
                        if link[query] is None:
                            await self.call(f"{'.'.join(cursor)}.{cmd}")
                        else:
                            await link[query](*cmd.split(" ")[1:])

                    continue

                # self.call(cmd)

            except Exception as e:
                print(e)
                continue


if __name__ == "__main__":
    runner = ApplicationRunner("ws://127.0.0.1:8080/ws", "realm1")
    runner.run(Console)

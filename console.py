import asyncio
from multiprocessing import dummy
from os import environ
import txaio

txaio.use_asyncio()
from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner
from autobahn.wamp.exception import ApplicationError

import types
import readline
import re
import gamestate
import pickle
from time import time
from math import floor


class Console(ApplicationSession):
    async def onJoin(self, details):
        async def peg_line(*args):
            try:
                y = int(args[0])
                spacing = int(args[1])
            except Exception:
                print("""Requires 2 arguments: y and spacing""")

            await self.call("builder.arena.tile.line", int(y), int(spacing))

        async def peg_place(*args):
            try:
                x = int(args[0])
                y = int(args[1])
            except Exception:
                print("""Requires 2 arguments: x and y""")
                return
            await self.call("builder.arena.tile", int(x), int(y))

        async def peg_clear(*args):
            try:
                if args[0] == "line":
                    y = int(args[1])
                    load = (y,)
                    call = "builder.arena.tile.clear.line"
                else:
                    x = int(args[0])
                    y = int(args[1])
                    load = (x, y)
                    call = "builder.arena.tile.clear"

            except Exception as e:
                print("""Requires 2 arguments: x and y""")
                return

            await self.call(call, *load)

        async def peg_grid(*args):
            x_spacing = 8
            y_spacing = 8
            try:
                if len(args) == 1:
                    x_spacing = int(args[0])
                elif len(args) == 2:
                    y_spacing = int(args[1])
            except Exception:
                print("""Requires 2 arguments: x_spacing and y_spacing""")

            await self.call("builder.arena.tile.grid", int(x_spacing), int(y_spacing))

        async def peg_random(*args):
            spacing = 6
            limit = 100
            try:
                if len(args) == 1:
                    spacing = int(args[0])
                elif len(args) == 2:
                    limit = int(args[1])
            except Exception:
                print("""Requires 2 arguments: spacing and limit""")

            await self.call("builder.arena.tile.random", int(spacing), int(limit))

        async def board_query(*args):
            try:
                key = args[0]
            except Exception:
                print("""Requires 1 argument: key""")
                return
            try:
                ret = await self.call("gamestate.get.key", key)
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

                    if key not in await self.call("gamestate.get"):
                        print(f"{key} is not a valid key in the board environment")
                        return

                    print(key, value)
                    if modificator == "=":
                        await self.call("gamestate.update.key", key, value)
                    else:
                        default_value = await self.call("gamestate.get.key", key)
                        await self.call(
                            "gamestate.update.key", key, int(default_value) + value
                        )

                    break

        async def place_player(*args):
            name = "dummy"

            try:
                x = int(args[0])
                y = int(args[1])
                if len(args) >= 3:
                    name = args[2]
            except Exception:
                print("""Requires 2 (+1) arguments: x, y and (name)""")
                return

            await self.call("spawn.player.place", int(x), int(y), display_name=name)

        async def place_random_player(*args):
            if len(args) > 0:
                name = args[0]
            else:
                name = "dummy"

            await self.call("spawn.player.random", name)

        async def place_slime(*args):

            try:
                x = int(args[0])
                y = int(args[1])
                if len(args) >= 3:
                    name = args[2]
                await self.call("spawn.slime.place", int(x), int(y), "console", name)
            except Exception:
                try:
                    name = args[0]
                    await self.call("spawn.slime.random", "console", name)
                except Exception:
                    await self.call("spawn.slime.random", "console")

        async def data_read_id(*args):

            start = time()

            try:
                id = int(args[0])
            except Exception as e:
                print("""Requires 1 argument: id""")
                return

            data = await self.call("data.player.read", id)

            print("======PLAYER INFO======")
            for item in data:
                print(f"o--> {item}: [{data[item]}]")
            print(f"=====TOOK {floor(time() - start)} SECONDS=====")

        async def get_alives(*args):
            start = time()
            ("======PLAYER ALIVES======")
            data = await self.call("gamestate.alives.get")
            for item in data:
                print(item)
            print(f"=====TOOK {floor(time() - start)} SECONDS=====")

        async def get_gamestate(*args):
            start = time()
            ("======GAME STATE======")
            data = await self.call("gamestate.get")
            print(data)
            print(f"=====TOOK {floor(time() - start)} SECONDS=====")

        async def data_update_id(*args):

            try:
                id = int(args[0])
                key = args[1]
                try:
                    value = int(args[2])
                except:
                    value = args[2]
                data = {key: value}
            except Exception as e:
                print("""Requires 3 argument: id, key and value""")
                return

            await self.call("data.player.update", id, data)
            await data_read_id(id)

        async def data_delete_id(*args):
            try:
                id = int(args[0])
            except Exception as e:
                print("""Requires 1 argument: id""")
                return

            await self.call("data.player.delete", id)

        architecture = {
            "builder": {
                "arena": {
                    "peg": {
                        "line": peg_line,
                        "place": peg_place,
                        "clear": peg_clear,
                        "grid": peg_grid,
                        "random": peg_random,
                    },
                    "clear": None,
                },
                "board": {
                    "construct": None,
                    "clear": None,
                    "query": board_query,
                    "set": board_set,
                },
                "default": None,
            },
            "spawn": {
                "player": {
                    "place": place_player,
                    "random": place_random_player,
                },
                "slime": {
                    "place": place_slime,
                    "random": place_slime,
                },
            },
            "data": {
                "player": {
                    "read": data_read_id,
                    "alives": get_alives,
                    "update": data_update_id,
                    "delete": data_delete_id,
                },
                "gamestate": {"get": get_gamestate},
            },
        }

        cursor = []
        link = architecture.copy()
        while True:
            try:

                def path():
                    return ".".join(cursor)

                pwd = path().replace(".", " -> ")
                cmd = input(f"[{pwd if pwd else 'root'}] ")

                if cmd == "":
                    continue

                def place(cursor):
                    link = architecture.copy()
                    for key in cursor:
                        link = link[key]
                    return link

                def list_commands(link):

                    cmds = []

                    found = None
                    for key in link:
                        if (
                            isinstance(link[key], types.FunctionType)
                            or link[key] is None
                        ):
                            cmds.append(key)
                            found = True

                    if cmds == []:
                        print(f"o--CMD--> [ / ]")
                        return

                    print(f'o--CMD--> [{" | ".join(cmds)}]')

                if cmd == "ls":

                    dirs = []
                    for key in link:
                        if type(link[key]) is dict:
                            dirs.append(key)

                    if dirs == []:
                        print(f"o--DIR--> [ / ]")
                        list_commands(link)
                        continue

                    print(f'o--DIR--> [{" | ".join(dirs)}]')
                    list_commands(link)
                    continue

                elif cmd.startswith("cd "):
                    arg = cmd.split(" ")[1]

                    if arg == "..":

                        cursor.pop()
                        link = place(cursor)

                    elif arg in link:
                        cursor.append(arg)
                        link = place(cursor)

                    continue

                elif cmd == "..":

                    cursor.pop()
                    link = place(cursor)

                elif cmd == "help":
                    print(
                        """
                    ls - list current directory
                    cd [directory] - change directory
                    help - show this help
                    """
                    )
                    continue
                elif cmd.startswith("/"):
                    arg = cmd[1:]
                    ret = await self.call("minecraft.post", arg)

                else:

                    query = cmd.split(" ")[0]
                    if query in link:
                        if link[query] is None:
                            await self.call(f"{'.'.join(cursor)}.{cmd}")
                        elif isinstance(link[query], types.FunctionType):
                            await link[query](*cmd.split(" ")[1:])
                        else:
                            cursor.append(query)
                            link = place(cursor)

                    continue

                print(cmd)
            except Exception as e:
                print(f"Exception: [{e}]")
                continue


if __name__ == "__main__":
    runner = ApplicationRunner("ws://127.0.0.1:8080/ws", "realm1")
    runner.run(Console)

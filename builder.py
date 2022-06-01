import asyncio
from os import environ
import txaio

txaio.use_asyncio()
from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner

import mcapi as mc
from random import randrange, choice
from math import floor
import pickle

from default_gamestate import default
from pyats.datastructures import AttrDict


class Builder(ApplicationSession):
    async def onJoin(self, details):

        ## ENV ##
        self.board = Board(await self.call("gamestate.get"), self)
        self.board.arena = Arena(self.board, self)
        

        await self.register(self.board.construct, "builder.board.construct")
        await self.register(self.board.deconstruct, "builder.board.clear")

        await self.register(self.board.arena.replace_tile, "builder.arena.tile.place")
        await self.register(self.board.arena.place_line, "builder.arena.tile.line")
        await self.register(
            self.board.arena.remove_tile_line, "builder.arena.tile.clear.line"
        )
        await self.register(self.board.arena.place_grid, "builder.arena.tile.grid")
        await self.register(self.board.arena.remove_tile, "builder.arena.tile.clear")
        await self.register(self.board.arena.random_tiles, "builder.arena.tile.random")
        await self.register(
            self.board.arena.replace_random, "builder.arena.tile.replace_random"
        )
        await self.register(self.board.arena.deconstruct, "builder.arena.clear")
        await self.subscribe(self.board.check_if_peg_message, "chat.message")
        await self.subscribe(self.board.construct, "gamestate.changed")
        await self.subscribe(self.board.trigger_next_round, "game.round.next")
        await self.register(self.board.load_default_env, "builder.default")
        await self.register(self.board.camera_place, "builder.camera.place")
        
    def onDisconnect(self):
        asyncio.get_event_loop().stop()


class Board:
    def __init__(self, env, builder):

        self.env = env
        self.builder = builder
        self.DEFAULT_TYPE = Peg

        try:
            self.compute_coords()
        except KeyError:
            print("Some keys couldn't be found, default env is loaded")
            self.builder.load_default_env()

    def camera_place(self):
        self.builder.call(
            "minecraft.post",
            f"execute as @e[name=funyrom] at @s run tp @s {self.env['origin_x'] - 44} {self.env['origin_y'] + 25} {self.env['origin_z'] + 41} -90 0",
        )

    async def trigger_next_round(self):
        # self.make_background()
        await self.arena.random_tiles()
        self.builder.call(
            "minecraft.post",
            f"execute as @e[tag=ball] at @s run tp @s ~ {self.env['height']} ~",
        )

    async def check_if_peg_message(self, message):
        message = pickle.loads(message)
        if "peg" in "".join(s for s in message["messageEx"] if isinstance(s, str)):
            await self.arena.replace_random()

    def load_default_env(self):
        self.builder.call("gamestate.update", default)

    def compute_coords(self):

        self.x1 = self.env["origin_x"]
        self.y1 = self.env["origin_y"]
        self.z1 = self.env["origin_z"]

        self.x2 = self.x1 + self.env["depth"] - 1
        self.y2 = self.y1 + self.env["height"] - 1
        self.z2 = self.z1 + self.env["width"] - 1

        self.board_zone = mc.Zone(
            (self.x1, self.y1, self.z1), (self.x2, self.y2, self.z2)
        )

        self.play_zone = mc.Zone(
            (self.x1, self.y1, self.z1), (self.x1, self.y2, self.z2)
        )

        self.peg_zone = mc.Zone(
            (
                self.x1,
                self.y1 + self.env["bottom_offset"],
                self.z1 + self.env["side_offset"],
            ),
            (
                self.x1,
                self.y2 - self.env["top_offset"],
                self.z2 - self.env["side_offset"],
            ),
        )

    async def deconstruct(self, *args):

        await self.arena.deconstruct()
        cmds = []

        for i in range(120):
            zone = mc.Zone(
                (self.x1 - 5, 0 + i, self.z1 - 5),
                (self.x2 + 5, 0 + i, self.z1 + 100),
            )
            cmds.append(mc._set_zone(zone, mc.Block("air"), "replace")["list"])

            if i == 3:
                cmds.append(
                    mc._set_zone(zone, mc.Block("grass_block"), "replace")["list"]
                )

        for cmd in cmds:
            for instruction in cmd:
                await self.builder.call("minecraft.post", instruction)

        self.builder.call(
            "minecraft.post", "execute as @e[type=!player] at @s run tp @s ~ 0 ~"
        )

    # Variable args to handle console input construct as well as change of env
    async def construct(self, *args):

        self.env = await self.builder.call("gamestate.get")
        await self.deconstruct()

        print("o-> Constructing board")

        self.compute_coords()

        structures = [
            self.make_cover,
            self.make_hollow_area,
            self.make_front_wall,
            self.make_back_wall,
            self.make_background,
            self.make_sides,
            self.make_bottom_bar,
        ]

        for structure in structures:
            cmds = structure()

        gen_terrain = True

        if len(args) == 1 and args[0] == "empty":
            gen_terrain = False

        if gen_terrain:
            await self.arena.random_tiles()
            await self.arena.replace_tile(FooDar(5, 5, self.builder))
     

    def make_cover(self):
        self.cover = {
            "zone": mc.Zone(
                (self.x1 - 1, self.y1, self.z1 - 3),
                (self.x2 + 2, self.y2 + 3, self.z2 + 3),
            ),
            "block": self.env["cover_block"],
        }

        cmds = mc._set_zone(self.cover["zone"], self.cover["block"], "replace")

        for instruction in cmds["list"]:
            self.builder.call("minecraft.post", instruction)
        return cmds

    def make_hollow_area(self):
        self.hollow_area = {
            "zone": mc.Zone(
                (self.x1, self.y1 - 4, self.z1 - 2), (self.x2, self.y2 + 2, self.z2 + 2)
            ),
            "block": self.env["hollow_area_block"],
        }

        cmds = mc._set_zone(
            self.hollow_area["zone"], self.hollow_area["block"], "replace"
        )
        for instruction in cmds["list"]:
            self.builder.call("minecraft.post", instruction)
        return cmds

    def make_front_wall(self):
        self.front_wall = {
            "zone": mc.Zone(
                (self.x1 - 1, self.y1 - 4, self.z1), (self.x1 - 1, self.y2, self.z2)
            ),
            "block": self.env["front_wall_block"],
        }

        cmds = mc._set_zone(
            self.front_wall["zone"], self.front_wall["block"], "replace"
        )
        for instruction in cmds["list"]:
            self.builder.call("minecraft.post", instruction)
        return cmds

    def make_back_wall(self):
        self.back_wall = {
            "zone": mc.Zone(
                (self.x2 + 1, self.y1 - 4, self.z1), (self.x2 + 1, self.y2, self.z2)
            ),
            "block": self.env["back_wall_block"],
        }

        cmds = mc._set_zone(self.back_wall["zone"], self.back_wall["block"], "replace")
        for instruction in cmds["list"]:
            self.builder.call("minecraft.post", instruction)
        return cmds

    def make_background(self):

        colors = [
            "orange",
            "magenta",
            "light_blue",
            "yellow",
            "lime",
            "pink",
            "gray",
            "light_gray",
            "cyan",
            "purple",
            "blue",
            "green",
            "red",
        ]

        color = randrange(len(colors))

        self.background = {
            "zone": mc.Zone(
                (self.x2 + 2, self.y1 - 4, self.z1), (self.x2 + 2, self.y2, self.z2)
            ),
            "block": self.env["background_block"],
        }

        colored_block_list = ["red_wool", "red_concrete"]
        if str(self.background["block"]) in colored_block_list:
            self.background["block"] = mc.Block(
                self.background["block"].replace(
                    "red",
                    colors[color],
                )
            )

        self.env["background_block"] = self.background["block"]
        cmds = mc._set_zone(
            self.background["zone"], self.background["block"], "replace"
        )

        for instruction in cmds["list"]:
            self.builder.call("minecraft.post", instruction)
        return cmds

    def make_sides(self):
        self.make_right_side()
        self.make_left_side()

    def make_right_side(self):
        self.make_right_bouncer()
        self.make_right_wall()
        self.make_right_cover()

    def make_right_bouncer(self):

        block = mc.Block(
            self.env["right_bouncer_block"],
            nbt=mc.NBT(
                {
                    "Command": 'execute if entity @e[distance=..3] run summon minecraft:tnt ~ ~-0.5 ~-1 {"fuse":0}',
                    "auto": 1,
                }
            ),
        )

        self.right_bouncer = {
            "block": block,
        }

        cmds = []
        for i in range(self.y1, self.y2 + 2):
            if i % self.env["bouncer_offset"] == 0:
                zone = mc.Zone((self.x1, i, self.z2 + 2), (self.x2, i, self.z2 + 2))
                cmds.append(mc._set_zone(zone, self.right_bouncer["block"], "replace"))

        for instruction in cmds:
            for cmd in instruction["list"]:
                self.builder.call("minecraft.post", cmd)
        return cmds

    def make_right_wall(self):
        self.right_wall = {
            "zone": mc.Zone(
                (self.x1, self.y1 - 4, self.z2 + 1), (self.x2, self.y2 + 6, self.z2 + 1)
            ),
            "block": self.env["right_wall_block"],
        }

        cmds = mc._set_zone(
            self.right_wall["zone"], self.right_wall["block"], "replace"
        )
        for instruction in cmds["list"]:
            self.builder.call("minecraft.post", instruction)
        return cmds

    def make_right_cover(self):

        block = mc.Block(self.env["right_cover_block"])

        block.blockstate = mc.BlockState(
            {"facing": "north", "half": "bottom", "open": "true"}
        )

        self.right_cover = {
            "block": block,
        }

        cmds = []
        for i in range(self.y1, self.y2 + 2):
            if i % self.env["bouncer_offset"] != 0:
                zone = mc.Zone((self.x1, i, self.z2), (self.x2, i, self.z2))
                cmds.append(mc._set_zone(zone, self.right_cover["block"], "replace"))

        for instruction in cmds:
            for cmd in instruction["list"]:
                self.builder.call("minecraft.post", cmd)
        return cmds

    def make_left_side(self):
        self.make_left_bouncer()
        self.make_left_wall()
        self.make_left_cover()

    def make_left_bouncer(self):

        block = mc.Block(
            self.env["left_bouncer_block"],
            nbt=mc.NBT(
                {
                    "Command": 'execute if entity @e[distance=..3] run summon minecraft:tnt ~ ~-0.5 ~1 {"fuse":0}',
                    "auto": 1,
                }
            ),
        )

        self.left_bouncer = {
            "block": block,
        }

        cmds = []
        for i in range(self.y1, self.y2 + 2):
            if i % self.env["bouncer_offset"] == 0:
                zone = mc.Zone((self.x1, i, self.z1 - 2), (self.x2, i, self.z1 - 2))
                cmds.append(mc._set_zone(zone, self.left_bouncer["block"], "replace"))

        for instruction in cmds:
            for cmd in instruction["list"]:
                self.builder.call("minecraft.post", cmd)
        return cmds

    def make_left_wall(self):
        self.left_wall = {
            "zone": mc.Zone(
                (self.x1, self.y1 - 4, self.z1 - 1), (self.x2, self.y2 + 6, self.z1 - 1)
            ),
            "block": self.env["left_wall_block"],
        }

        cmds = mc._set_zone(self.left_wall["zone"], self.left_wall["block"], "replace")
        for instruction in cmds["list"]:
            self.builder.call("minecraft.post", instruction)
        return cmds

    def make_left_cover(self):

        block = mc.Block(self.env["left_cover_block"])

        block.blockstate = mc.BlockState(
            {"facing": "south", "half": "bottom", "open": "true"}
        )

        self.left_cover = {
            "block": block,
        }

        cmds = []
        for i in range(self.y1, self.y2 + 2):
            if i % self.env["bouncer_offset"] != 0:
                zone = mc.Zone((self.x1, i, self.z1), (self.x2, i, self.z1))
                cmds.append(mc._set_zone(zone, self.left_cover["block"], "replace"))

        for instruction in cmds:
            for cmd in instruction["list"]:
                self.builder.call("minecraft.post", cmd)
        return cmds

    def make_bottom_bar(self):
        self.bottom_bar = {
            "zone": mc.Zone(
                (self.x1 - 1, self.y1 + 2, self.z1), (self.x1 - 1, 0, self.z2)
            ),
            "block": self.env["bottom_bar_block"],
        }

        cmds = mc._set_zone(
            self.bottom_bar["zone"], self.bottom_bar["block"], "replace"
        )
        for instruction in cmds["list"]:
            self.builder.call("minecraft.post", instruction)
        return cmds


class Arena:
    def __init__(self, board, builder):
        self.board = board

        x = self.board.play_zone.pos2.y + 1
        y = self.board.play_zone.pos2.z + 1
        self.builder = builder

        self.DEFAULT_TYPE = Peg

        self.plate = []

        for i in range(x):
            self.plate.append([])
            for j in range(y):
                self.plate[i].append(Empty(i, j, self.builder))
                
        
        
        

    async def deconstruct(self):

        print("o---> Deconstructing arena")

        for i in range(len(self.plate)):
            for j in range(len(self.plate[i])):
                await self.replace_tile(Empty(i, j, self.builder))

    async def replace_random(self):
        def check_distance(coord, pegs, distance=4):
            for peg in pegs:
                if (
                    abs(coord[0] - peg[0]) < distance
                    and abs(coord[1] - peg[1]) < distance
                ):
                    return False

            return True

        pegs = []
        for line in self.plate:
            for tile in line:
                if isinstance(tile, Peg):
                    pegs.append(tile)

        x1 = randrange(
            0 + self.board.env["bottom_offset"],
            len(self.plate) - self.board.env["top_offset"],
        )
        y1 = randrange(
            0 + self.board.env["side_offset"],
            len(self.plate[0]) - self.board.env["side_offset"],
        )

        pegs_as_coords = [(item.x, item.y) for item in pegs]
        max_tries = 1000
        tried = 0
        while not check_distance((x1, y1), pegs_as_coords):
            x1 = randrange(
                0 + self.board.env["bottom_offset"],
                len(self.plate) - self.board.env["top_offset"],
            )
            y1 = randrange(
                0 + self.board.env["side_offset"],
                len(self.plate[0]) - self.board.env["side_offset"],
            )
            tried += 1
            if tried > max_tries:
                break

        if len(pegs) <= 1:
            print("Fix this error")
            return []

        chosen = randrange(0, len(pegs) - 1)

        x2 = pegs[chosen].x
        y2 = pegs[chosen].y

        await self.replace_tile(Empty(x2, y2, self.builder))
        cmd = f'particle minecraft:witch {self.board.env["origin_x"]} {x2} {y2} 1.2 1.2 1.2 0.5 400 force'
        self.builder.call("minecraft.post", cmd)

        await self.replace_tile(Peg(x1, y1, self.builder))
        cmd = f'particle minecraft:witch {self.board.env["origin_x"]} {x1} {y1} 1.2 1.2 1.2 0.5 400 force'
        self.builder.call("minecraft.post", cmd)

    async def replace_tile(self, tile):

        x = tile.x
        y = tile.y

        tile.board = self.board

        old_tile = self.plate[x][y]
        cmd = old_tile.remove()

        cmds = []
        if cmd:
            for instruction in cmd:
                for cmd in instruction["list"]:
                    cmds.append(cmd)
                    await self.builder.call("minecraft.post", cmd)

        self.plate[x][y] = tile
        cmd = tile.place()

        if cmd:
            for instruction in cmd:
                for cmd in instruction["list"]:
                    cmds.append(cmd)
                    await self.builder.call("minecraft.post", cmd)

        nest = mc.functions.base_functions.nest_commands(cmds)
        coords = mc.BlockCoordinates(self.board.env["origin_x"] + 5, x, y)
        cmd = mc.functions.base_functions.format_nest(coords, nest)
        # print(cmd, len(cmd))
        # ret = await self.builder.call("minecraft.post", cmd)
        # print("ret: ", ret)

    def remove_tile_line(self, y, tile_type=None):
        if tile_type is None:
            tile_type = DEFAULT_TILE_TYPE

        cmds = []

        for i in range(len(self.plate[y])):
            self.remove_tile(y, i, tile_type)

        print(f"Removing line of tiles at y={y}")

    async def remove_tile(self, x, y, tile_type=None):
        if tile_type is None:
            tile_type = DEFAULT_TILE_TYPE

        cmds = []
        print(f"Removing tile at {x} {y}")
        if isinstance(self.plate[x][y], tile_type) or tile_type == None:
            await self.replace_tile(Empty(x, y))

    async def place_line(
        self, y, spacing=8, tile_type=None, limit=None, even_policy="random"
    ):
        if tile_type is None:
            tile_type = DEFAULT_TILE_TYPE

        peg_line = []

        width = len(self.plate[0]) - self.board.env["side_offset"] * 2

        i = 0
        n_to_place = 0
        while i + spacing < width:
            i += spacing
            n_to_place += 1
            if limit and n_to_place >= limit:
                break

        rest = width - i
        left_padding = floor(rest / 2)
        right_padding = left_padding

        if rest % 2:
            if even_policy == "random":
                if choice([0, 1]):
                    left_padding += 1
                else:
                    right_padding += 1
            elif even_policy == "left":
                left_padding += 1
            elif even_policy == "right":
                right_padding += 1

        class_lookup = {"class_name": tile_type}
        casted_type = class_lookup["class_name"]

        for _ in range(left_padding):
            peg_line.append(Empty(y, len(peg_line) + self.board.env["side_offset"]))

        for _ in range(n_to_place):
            peg_line.append(
                casted_type(y, len(peg_line) + self.board.env["side_offset"], self.builder)
            )
            for _ in range(spacing - 1):
                peg_line.append(Empty(y, len(peg_line) + self.board.env["side_offset"], self.builder))

        peg_line.append(casted_type(y, len(peg_line) + self.board.env["side_offset"], self.builder))

        for _ in range(left_padding):
            peg_line.append(Empty(y, len(peg_line) + self.board.env["side_offset"], self.builder))

        cmds = []
        for tile in peg_line:
            await self.replace_tile(tile)

        print(f"o---> Placing line of tiles with y={y} with spacing={spacing}")

    async def place_grid(
        self,
        x_spacing=10,
        y_spacing=10,
        tile_type=None,
        limit=None,
        even_policy="random",
    ):

        if tile_type is None:
            tile_type = DEFAULT_TILE_TYPE

        await self.deconstruct()

        height = (
            len(self.plate)
            - self.board.env["top_offset"]
            - self.board.env["bottom_offset"]
        )

        i = 0
        n_to_place = 0
        while i + x_spacing < height:
            i += x_spacing
            n_to_place += 1
            if limit and n_to_place >= limit:
                break

        rest = height - i
        top_padding = floor(rest / 2)
        bottom_padding = top_padding

        if rest % 2:
            if even_policy == "random":
                if choice([0, 1]):
                    top_padding += 1
                else:
                    bottom_padding += 1
            elif even_policy == "left":
                top_padding += 1
            elif even_policy == "right":
                bottom_padding += 1

        class_lookup = {"class_name": tile_type}
        casted_type = class_lookup["class_name"]

        y = 0
        for _ in range(top_padding):
            await self.place_line(
                y + self.board.env["bottom_offset"],
                y_spacing,
                Empty,
                limit,
                even_policy,
            )

            y += 1

        for _ in range(n_to_place):
            await self.place_line(
                y + self.board.env["bottom_offset"],
                y_spacing,
                casted_type,
                limit,
                even_policy,
            )

            y += 1
            for _ in range(x_spacing - 1):

                await self.place_line(
                    y + self.board.env["bottom_offset"],
                    y_spacing,
                    Empty,
                    limit,
                    even_policy,
                )

                y += 1

        await self.place_line(
            y + self.board.env["bottom_offset"],
            y_spacing,
            Peg,
            limit,
            even_policy,
        )

        y += 1

        for _ in range(top_padding):
            await self.place_line(
                y + self.board.env["bottom_offset"],
                y_spacing,
                Empty,
                limit,
                even_policy,
            )
            y += 1

        print(f"o---> Placing grid of tiles with x={x_spacing} y={y_spacing}")

    async def random_tiles(self, spacing=6, limit=100, tile_type=None):

        if tile_type is None:
            tile_type = DEFAULT_TILE_TYPE

        await self.deconstruct()
        cmds = []

        def check_distance(coord, pegs, distance=3):
            for peg in pegs:
                if (
                    abs(coord[0] - peg[0]) < distance
                    and abs(coord[1] - peg[1]) < distance
                ):
                    return False

            return True

        tried = 0
        max_tries = 10000
        list_of_pegs = []

        while True:
            pegy = randrange(
                0 + self.board.env["bottom_offset"],
                len(self.plate) - self.board.env["top_offset"],
            )
            pegz = randrange(
                0 + self.board.env["side_offset"],
                len(self.plate[0]) - self.board.env["side_offset"],
            )

            if check_distance((pegy, pegz), list_of_pegs, spacing):
                list_of_pegs.append((pegy, pegz))

            if tried == max_tries or tried > limit:
                break

            tried += 1

        class_lookup = {"class_name": tile_type}
        casted_type = class_lookup["class_name"]

        for peg in list_of_pegs:
            await self.replace_tile(casted_type(peg[0], peg[1], self.builder))

        print(f"o---> Placing random tiles with spacing={spacing} limit={limit}")


class Tile:
    def __init__(self, x, y, builder):
        self.builder = builder
        self.board = builder.board
        self.x = x
        self.y = y

    def remove(self):
        cmds = []

        if self.__dir__():
            for attr in self.__dir__():
                obj = getattr(self, attr)
                if type(obj) is dict:
                    if "replace" in obj:
                        block = obj["replace"]
                    else:
                        block = mc.Block("air")

                    if "coords" in obj:
                        cmds.append(mc._set_block(obj["coords"], block, "replace"))
                    elif "zone" in obj:
                        cmds.append(mc._set_zone(obj["zone"], block, "replace"))

        return cmds


class Peg(Tile):
    def place(self):

        cmds = []

        x1, y1, z1 = (self.board.x1, self.x, self.y)
        x2 = self.board.x2

        # Peg repulsion handler
        peg_block = mc.Block(
            "repeating_command_block",
            nbt=mc.NBT(
                {
                    "Command": f"execute if entity @e[x={x1}, y={y1 - 2}, z={z1 - 2}, dx={x2}, dy=3, dz=3] run summon minecraft:tnt ~-{self.board.env['depth'] - 1 / 2} ~ ~ "
                    + "{Fuse:0b}",
                    "auto": 1,
                }
            ),
            blockstate=mc.BlockState({"facing": "east"}),
        )

        coords = mc.BlockCoordinates(x2 + 2, y1, z1)

        self.peg_block = {
            "block": peg_block,
            "coords": coords,
            "replace": self.board.env["background_block"],
        }

        cmd = mc._set_block(coords, peg_block, "replace")
        cmds.append(cmd)

        # Peg particle handler
        particle_block = mc.Block(
            "chain_command_block",
            nbt=mc.NBT(
                {
                    "Command": "particle minecraft:crit ~-3 ~ ~ 0.5 0.6 0.6 0.05 250 force",
                    "auto": 1,
                }
            ),
            blockstate=mc.BlockState({"conditional": True, "facing": "east"}),
        )

        coords = mc.BlockCoordinates(x2 + 3, y1, z1)
        self.particle_block = {"block": particle_block, "coords": coords}
        cmds.append(mc._set_block(coords, particle_block, "replace"))

        # Peg hitbox
        zone = mc.Zone((x1, y1 - 1, z1), (x2, y1 - 1, z1))
        self.peg_hitbox = {"block": mc.Block("barrier"), "zone": zone}
        cmds.append(mc._set_zone(zone, mc.Block("barrier"), "replace"))

        # Peg decoration block
        zone = mc.Zone((x2 + 1, y1 + 1, z1 - 1), (x2 + 1, y1 - 1, z1 + 1))
        self.peg_decoration = {
            "block": self.board.env["peg_block"],
            "zone": zone,
            "replace": self.board.env["back_wall_block"],
        }
        cmds.append(mc._set_zone(zone, self.board.env["peg_block"], "replace"))

        return cmds


DEFAULT_TILE_TYPE = Peg

class FooDar(Tile):
        def __init__(self, x, y, builder):
            
            print("creating a foooodar")
            self.builder = builder
            super().__init__(x, y, builder)
            
            print("creating a foooodar")
            
            self.x = self.board.env['origin_x'] + self.board.env['depth']
            self.y = self.board.env['origin_y'] + self.board.env['height']
            self.z = self.board.env['origin_z'] + self.board.env['width']
            
            self.builder.subscribe(self.up, 'foodar.up')
            self.builder.subscribe(self.down, 'foodar.down')
            self.builder.subscribe(self.left, 'foodar.left')
            self.builder.subscribe(self.right, 'foodar.right')
            
       
            
        def place(self):
            self.builder.call('minecraft.post', f"setblock {self.x} {self.y} {self.z} red_concrete")
            block = mc.Block("stone")
            coords = mc.BlockCoordinates(self.x, self.y, self.z)
            
            self.block_to_remove = {
                "block": block,
                "coords": coords,
                "replace": self.board.env["background_block"],
        }
            
        
            
            
        def up(self):
            print("hellozer")
            new_y = self.y + 1
            if new_y < self.board.env['height'] - self.board.env['top_offset']:
                self.move(self.x, new_y, self.z)
        def down(self):
            new_y = self.y - 1
            if new_y >= (0 + self.board.env['bottom_offset']):
                self.move(self.x, new_y, self.z)
                
        def right(self):
            new_z = self.z + 1
            if new_z >= 0 + self.board.env['bottom_offset']:
                self.move(self.x, self.y, new_z)        
        def left(self):
            new_z = self.z - 1
            if new_z < self.board.env['origin_z'] + self.board.env['height'] :
                self.move(self.x, self.y, new_z)
        
                    
        


class Empty(Tile):
    def place(self):
        return []


if __name__ == "__main__":
    runner = ApplicationRunner("ws://127.0.0.1:8080/ws", "realm1")
    runner.run(Builder)

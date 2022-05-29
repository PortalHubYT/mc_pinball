import asyncio
from os import environ
import txaio

txaio.use_asyncio()
from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner

import mcapi as mc
from random import randrange, choice
from math import floor
import pickle
import gamestate


class Builder(ApplicationSession):
    async def onJoin(self, details):
        self.env = await gamestate.create(self)

        ## BOARD ##

        self.board = Board(self.env)
        self.arena = Arena(self.board)

        # Variable args to handle console input construct as well as change of env
        def board_constructer(*args):
            board_deconstructer()

            instructions = self.board.construct()
            for cmd in instructions:
                self.call("minecraft.post", cmd)

            self.arena = Arena(self.board)
            arena_constructer()

        def board_deconstructer():
            arena_deconstructer()

            instructions = self.board.deconstruct()
            for cmd in instructions:
                self.call("minecraft.post", cmd)

        def board_editor(key, value, mod):
            self.call("gamestate.write", "builder", key, value, mod)

        # This should read attributes of Board instead or bonus
        def board_reader(key):
            return self.call("gamestate.read", "builder", key)

        def board_getter():
            return pickle.dumps(self.board)

        await self.register(board_constructer, "board.construct")
        await self.register(board_deconstructer, "board.deconstruct")
        await self.register(board_editor, "board.edit")
        await self.register(board_reader, "board.read")
        await self.register(board_getter, "board.get")

        ## ARENA ##

        def arena_constructer():

            arena_deconstructer()
            instructions = self.arena.construct()
            for cmd in instructions:
                self.call("minecraft.post", cmd)

        def arena_deconstructer():
            instructions = self.arena.deconstruct()
            for cmd in instructions:
                self.call("minecraft.post", cmd)

        def arena_peg_placer(x, y):
            arena_peg_remover(x, y)
            instructions = self.arena.replace_tile(Peg(x, y))
            for instruction in instructions:
                for cmd in instruction["list"]:
                    self.call("minecraft.post", cmd)

        def arena_peg_line_placer(y, spacing, limit=None):
            arena_peg_line_remover(y)
            instructions = self.arena.place_line_peg(y, spacing, limit)
            for instruction in instructions:
                for cmd in instruction["list"]:
                    self.call("minecraft.post", cmd)

        def arena_peg_remover(x, y):
            instructions = self.arena.remove_tile(x, y, Peg)
            for instruction in instructions:
                for cmd in instruction["list"]:
                    self.call("minecraft.post", cmd)

        def arena_peg_line_remover(y):
            instructions = self.arena.remove_tile_line(y, Peg)
            for instruction in instructions:
                for cmd in instruction["list"]:
                    self.call("minecraft.post", cmd)

        await self.register(arena_peg_placer, "arena.place_peg")
        await self.register(arena_peg_line_placer, "arena.place_peg_line")
        await self.register(arena_peg_line_remover, "arena.remove_peg_line")
        await self.register(arena_peg_remover, "arena.remove_peg")
        await self.register(arena_constructer, "arena.construct")
        await self.register(arena_deconstructer, "arena.deconstruct")

        await self.subscribe(board_constructer, "gamestate.sync")

    def onDisconnect(self):
        asyncio.get_event_loop().stop()


class Board:
    def __init__(self, env):

        self.env = env

        self.compute_coords()

    def compute_coords(self):

        self.x1 = self.env.origin_x
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

    def deconstruct(self):
        cmds = []

        for i in range(255):
            zone = mc.Zone(
                (self.x1 - 5, 0 + i, self.z1 - 5),
                (self.x2 + 5, 0 + i, self.z1 + 100),
            )
            cmds.extend(mc._set_zone(zone, mc.Block("air"), "replace")["list"])

            if i == 3:
                cmds.extend(
                    mc._set_zone(zone, mc.Block("grass_block"), "replace")["list"]
                )

        return cmds

    def construct(self):

        instructions = []

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

            if type(cmds) is dict:
                cmds = [cmds]

            for instruction in cmds:

                for cmd in instruction["list"]:
                    instructions.append(cmd)

        return instructions

    def make_cover(self):
        self.cover = {
            "zone": mc.Zone(
                (self.x1 - 1, self.y1, self.z1 - 3),
                (self.x2 + 2, self.y2 + 3, self.z2 + 3),
            ),
            "block": self.env["cover_block"],
        }

        cmds = mc._set_zone(self.cover["zone"], self.cover["block"], "replace")
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
        return cmds

    def make_back_wall(self):
        self.back_wall = {
            "zone": mc.Zone(
                (self.x2 + 1, self.y1 - 4, self.z1), (self.x2 + 1, self.y2, self.z2)
            ),
            "block": self.env["back_wall_block"],
        }

        cmds = mc._set_zone(self.back_wall["zone"], self.back_wall["block"], "replace")
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

        colored_block_list = ["minecraft:white_wool", "minecraft:white_concrete"]
        if str(self.background["block"]) in colored_block_list:
            self.background["block"] = mc.Block(
                self.background["block"].replace(
                    "white",
                    colors[color],
                )
            )

        cmds = mc._set_zone(
            self.background["zone"], self.background["block"], "replace"
        )

        return cmds

    def make_sides(self):
        cmds = []
        cmds.extend(self.make_right_side())
        cmds.extend(self.make_left_side())
        return cmds

    def make_right_side(self):
        cmds = []
        cmds.extend(self.make_right_bouncer())
        cmds.append(self.make_right_wall())
        cmds.extend(self.make_right_cover())
        return cmds

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

        return cmds

    def make_left_side(self):
        cmds = []
        cmds.extend(self.make_left_bouncer())
        cmds.append(self.make_left_wall())
        cmds.extend(self.make_left_cover())
        return cmds

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

        return cmds

    def make_left_wall(self):
        self.left_wall = {
            "zone": mc.Zone(
                (self.x1, self.y1 - 4, self.z1 - 1), (self.x2, self.y2 + 6, self.z1 - 1)
            ),
            "block": self.env["left_wall_block"],
        }

        cmds = mc._set_zone(self.left_wall["zone"], self.left_wall["block"], "replace")
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
        return cmds


class Arena:
    def __init__(self, board):
        self.board = board

        x = self.board.play_zone.pos2.y + 1
        y = self.board.play_zone.pos2.z + 1

        self.plate = []

        for i in range(x):
            self.plate.append([])
            for j in range(y):
                self.plate[i].append(Empty(i, j))

    def deconstruct(self):
        return []

    def construct(self):
        return []

    def replace_tile(self, tile):

        cmds = []

        x = tile.x
        y = tile.y
        tile.board = self.board

        old_tile = self.plate[x][y]
        cmd = old_tile.remove()
        cmds.extend(cmd)

        self.plate[x][y] = tile
        cmd = tile.place()
        cmds.extend(cmd)

        return cmds

    def remove_tile_line(self, y, type=None):
        cmds = []

        for i in range(len(self.plate[y])):
            cmds.extend(self.remove_tile(y, i, type))

        return cmds

    def remove_tile(self, x, y, type=None):
        cmds = []

        if isinstance(self.plate[x][y], type) or type == None:

            cmd = self.replace_tile(Empty(x, y))
            cmds.extend(cmd)

        return cmds

    def place_line_peg(self, y, spacing=8, limit=None, even_policy="random"):

        cmds = []

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

        for _ in range(left_padding):
            peg_line.append(Empty(y, len(peg_line) + self.board.env["side_offset"]))

        for _ in range(n_to_place):
            peg_line.append(Peg(y, len(peg_line) + self.board.env["side_offset"]))
            for _ in range(spacing - 1):
                peg_line.append(Empty(y, len(peg_line) + self.board.env["side_offset"]))

        peg_line.append(Peg(y, len(peg_line) + self.board.env["side_offset"]))

        for _ in range(left_padding):
            peg_line.append(Empty(y, len(peg_line) + self.board.env["side_offset"]))

        cmds = []
        for tile in peg_line:
            cmd = self.replace_tile(tile)
            cmds.extend(cmd)

        return cmds


class Tile:
    def __init__(self, x, y, board=None):
        self.board = board
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
        cmds.append(mc._set_block(coords, peg_block, "replace"))

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


class Empty(Tile):
    def place(self):
        return []


if __name__ == "__main__":
    runner = ApplicationRunner("ws://127.0.0.1:8080/ws", "realm1")
    runner.run(Builder)

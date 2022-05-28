import asyncio
from os import environ
import txaio

txaio.use_asyncio()
from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner

import mcapi as mc
from random import randrange
from math import floor


class Builder(ApplicationSession):
    async def onJoin(self, details):

        self.board = Board()

        def board_constructer():
            instructions = self.board.construct()
            for cmd in instructions:
                self.call("minecraft.post", cmd)

        def board_deconstructer():
            instructions = self.board.deconstruct()
            for cmd in instructions:
                self.call("minecraft.post", cmd)

        def board_editor(key, value):
            self.board.edit(key, value)

        def board_reader(info):
            return self.board.read(info)

        await self.subscribe(board_constructer, "construct")
        await self.subscribe(board_deconstructer, "deconstruct")
        await self.register(board_editor, "edit")
        await self.register(board_reader, "read")

    def onDisconnect(self):
        asyncio.get_event_loop().stop()


class Board:
    def __init__(self):

        self.env = {
            "origin": mc.BlockCoordinates(0, 4, 0),
            "width": 68,
            "height": 46,
            "depth": 2,
            "bouncer_offset": 4,
            "peg_block": mc.Block("sea_lantern"),
            "play_area_block": mc.Block("air"),
            "front_wall_block": mc.Block("barrier"),
            "back_wall_block": mc.Block("barrier"),
            "background_block": mc.Block("red_concrete"),
            "cover_block": mc.Block("smooth_quartz"),
            "bottom_bar_block": mc.Block("smooth_quartz"),
            "right_bouncer_block": mc.Block("repeating_command_block"),
            "right_wall_block": mc.Block("air"),
            "right_cover_block": mc.Block("oak_trapdoor"),
            "left_bouncer_block": mc.Block("repeating_command_block"),
            "left_wall_block": mc.Block("air"),
            "left_cover_block": mc.Block("oak_trapdoor"),
        }

        self.compute_coords()

    def compute_coords(self):
        self.origin = self.env["origin"]

        self.depth = self.env["depth"]
        self.height = self.env["height"]
        self.width = self.env["width"]

        self.x1, self.y1, self.z1 = self.origin.set

        self.x2 = self.x1 + self.depth - 1
        self.y2 = self.y1 + self.height - 1
        self.z2 = self.z1 + self.width - 1

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
        instructions.extend(self.deconstruct())

        self.compute_coords()

        structures = [
            self.make_cover,
            self.make_play_area,
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

    def edit(self, key, value):

        if key not in self.env:
            print(f"{key} is not a valid key in the board environment")
            return

        if type(self.env[key]) is int:
            self.env[key] = int(value)
        elif type(self.env[key]) is mc.Block:
            self.env[key].id = value
        elif type(self.env[key]) is mc.BlockCoordinates:
            self.env[key].x = value.split(",")[0]
            self.env[key].y = value.split(",")[1]
            self.env[key].z = value.split(",")[2]

        self.compute_coords()

    def read(self, key):
        return self.env[key]

    def place_peg(self, x, y):

        cmds = []

        x1, y1, z1 = (self.x1, x, y)
        x2 = self.x2

        # Peg repulsion handler
        peg_block = mc.Block(
            "repeating_command_block",
            nbt=mc.NBT(
                {
                    "Command": f"execute if entity @e[x={x1}, y={y1 - 2}, z={z1 - 2}, dx={x2}, dy=3, dz=3] run summon minecraft:tnt ~-{self.env['depth'] - 1 / 2} ~ ~ "
                    + "{Fuse:0b}",
                    "auto": 1,
                }
            ),
            blockstate=mc.BlockState({"facing": "east"}),
        )

        coords = mc.BlockCoordinates(x2 + 2, y1, z1)
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
        cmds.append(mc._set_block(coords, particle_block, "replace"))

        # Peg hitbox
        zone = mc.Zone((x1, y1 - 1, z1), (x2, y1 - 1, z1))
        cmds.append(mc._set_zone(zone, mc.Block("barrier"), "replace"))

        # Peg decoration block
        zone = mc.Zone((x2 + 1, y1 + 1, z1 - 1), (x2 + 1, y1 - 1, z1 + 1))
        cmds.append(mc._set_zone(zone, self.env["peg_block"], "replace"))

        return cmds

    def place_line_peg(self, y, distance=8):
        pegs = floor(width / distance)
        spacing = floor((pegs * distance) / pegs)

        width = 20

    def generate_pegs(self):
        pass

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

    def make_play_area(self):
        self.play_area = {
            "zone": mc.Zone(
                (self.x1, self.y1 - 4, self.z1 - 2), (self.x2, self.y2 + 2, self.z2 + 2)
            ),
            "block": self.env["play_area_block"],
        }

        cmds = mc._set_zone(self.play_area["zone"], self.play_area["block"], "replace")
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
            "block": self.env["background_block"].id.replace(
                "red" if "concrete" in self.env["background_block"].id else "",
                colors[color],
            ),
        }

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

        block = self.env["right_bouncer_block"].id
        block = mc.Block(
            block,
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

        block = self.env["right_cover_block"].id
        block = mc.Block(block)

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

        block = self.env["left_bouncer_block"].id
        block = mc.Block(
            block,
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

        block = self.env["left_cover_block"].id
        block = mc.Block(block)

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


if __name__ == "__main__":
    runner = ApplicationRunner("ws://127.0.0.1:8080/ws", "realm1")
    runner.run(Builder)

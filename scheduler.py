import asyncio
from os import environ
import txaio
from time import time
from math import floor
import random

txaio.use_asyncio()

from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner


class Scheduler(ApplicationSession):
    def respawn_portalhub_randomly(self):
        x = (self.gamestate["origin_x"] + self.gamestate["depth"]) / 2
        y = self.gamestate["origin_y"] + self.gamestate["height"] - 3
        z = random.randrange(self.gamestate["origin_z"], self.gamestate["width"])

        self.call("minecraft.post", f"tp portalhub {x}{y}{z}")

    wait_time = 0.1

    async def onJoin(self, details):

        i = 0
        while True:
            start = time()
            # if i % 5 == 0:

            print(str("*" * (i % 15)).ljust(15), end="")
            if i % 10 == 0:
                self.publish("game.tick")

                self.gamestate = await self.call("gamestate.get")

                self.call(
                    "minecraft.post",
                    f"bossbar set minecraft:peglin value {int((i % 1000) / 10)}",
                )

            # if i % 50 == 0:
            # self.call('minecraft.post', f"scoreboard players reset * alive_for")

            if i % 2000 == 0:
                self.publish("data.commit")
                self.publish("game.round.next")
                f'title funyrom title "New round"',
                f'title funyrom subtitle "Any message in chat will spawn you"',

            i += 1
            await asyncio.sleep(self.wait_time)
            print(f"[Last {floor(time() - start)}s, expected {floor(self.wait_time)}s]")


# txaio.use_asyncio()

if __name__ == "__main__":
    runner = ApplicationRunner("ws://127.0.0.1:8080/ws", "realm1")
    runner.run(Scheduler)

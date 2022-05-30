import asyncio
from os import environ
import txaio
from time import time
from math import floor

txaio.use_asyncio()

from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner


class Scheduler(ApplicationSession):

    wait_time = 1
    

    async def onJoin(self, details):
        i = 0
        while True:
            start = time()
            self.publish("game.tick")
            print(str("*" * (i % 10)).ljust(10), end="")
            print(f"game.tick ", end="")
            i += 1
            await asyncio.sleep(self.wait_time)
            print(f"[Last {floor(time() - start)}s, expected {floor(self.wait_time)}s]")


# txaio.use_asyncio()

if __name__ == "__main__":
    runner = ApplicationRunner("ws://127.0.0.1:8080/ws", "realm1")
    runner.run(Scheduler)

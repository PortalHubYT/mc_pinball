import asyncio
from os import environ
import txaio

txaio.use_asyncio()

from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner


class Scheduler(ApplicationSession):
    """
    An application component that publishes an event every second.
    """

    async def onJoin(self, details):

        while True:
            self.publish("scheduler.game_tick")
            await asyncio.sleep(20)


# txaio.use_asyncio()

if __name__ == "__main__":
    runner = ApplicationRunner("ws://127.0.0.1:8080/ws", "realm1")
    runner.run(Scheduler)

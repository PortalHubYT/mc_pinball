import asyncio
from os import environ
import txaio
txaio.use_asyncio()
from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner


class Component(ApplicationSession):
    """
    An application component calling the different backend procedures.
    """

    async def onJoin(self, details):

        await self.call('com.arguments.ping')
        print("Pinged!")

        res = await self.call('com.arguments.add2', 2, 3)
        print("Add2: {}".format(res))



        self.leave()

    def onDisconnect(self):
        asyncio.get_event_loop().stop()


if __name__ == '__main__':
    runner = ApplicationRunner("ws://127.0.0.1:8080/ws", "realm1")
    runner.run(Component)
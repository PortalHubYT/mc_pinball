import asyncio
from os import environ
import txaio
txaio.use_asyncio()
from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner
import gamestate

class Component(ApplicationSession):
    """
    An application component providing procedures with different kinds
    of arguments.
    """

    async def onJoin(self, details):
        self.gamestate = await gamestate.create(self)

        def ping():
            return

        def add2(a, b):
            return a + b

        def stars(nick="somebody", stars=0):
            return "{} starred {}x".format(nick, stars)

        # noinspection PyUnusedLocal
        def orders(product, limit=5):
            return ["Product {}".format(i) for i in range(50)][:limit]

        def arglen(*args, **kwargs):
            return [len(args), len(kwargs)]

        await self.register(ping, 'com.arguments.ping')
        await self.register(add2, 'com.arguments.add2')
        await self.register(stars, 'com.arguments.stars')
        await self.register(orders, 'com.arguments.orders')
        await self.register(arglen, 'com.arguments.arglen')
        print("Registered methods; ready for frontend.")


if __name__ == '__main__':
    runner = ApplicationRunner("ws://127.0.0.1:8080/ws", "realm1")
    runner.run(Component)
import asyncio
from os import environ
import txaio
txaio.use_asyncio()
from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner
import time
import gamestate


import default_gamestate
from pyats.datastructures import AttrDict

import inspect
class Component(ApplicationSession):

    async def onJoin(self, details):
        import gamestate
        g = await gamestate.create(self)
        
        while True:
            
            print(g)
            await asyncio.sleep(1)
            print("\n"  * 20)

    def onDisconnect(self):
        asyncio.get_event_loop().stop()


if __name__ == '__main__':
    runner = ApplicationRunner("ws://127.0.0.1:8080/ws", "realm1")
    runner.run(Component)
import asyncio
import txaio
txaio.use_asyncio()
from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner

class Component(ApplicationSession):

    async def onJoin(self, details):
        pass

    def onDisconnect(self):
        asyncio.get_event_loop().stop()

if __name__ == '__main__':
    runner = ApplicationRunner("ws://127.0.0.1:8080/ws", "realm1")
    runner.run(Component)
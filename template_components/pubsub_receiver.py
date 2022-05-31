import asyncio
from os import environ
import txaio
txaio.use_asyncio()
from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner

class Component(ApplicationSession):

    async def onJoin(self, details):
        self.received = 0

        def on_event(i):
            print(" Pig1 Got event: {}".format(i))
            self.received += 1
            if self.received > 5:
                self.leave()

        await self.subscribe(on_event, 'com.myapp.topic1')

    def onDisconnect(self):
        asyncio.get_event_loop().stop()


if __name__ == '__main__':
    runner = ApplicationRunner("ws://127.0.0.1:8080/ws", "realm1")
    runner.run(Component)
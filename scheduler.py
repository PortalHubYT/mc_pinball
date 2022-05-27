import asyncio
from os import environ
import txaio
txaio.use_asyncio()

from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner



class Component(ApplicationSession):
    """
    An application component that publishes an event every second.
    """

    async def onJoin(self, details):
        counter = 0
        while True:
            print("publish: com.myapp.topic1", counter)
            self.publish('com.myapp.topic1', counter)
            counter += 1
            await asyncio.sleep(1)
        

# txaio.use_asyncio()

if __name__ == '__main__':
    
    url = environ.get("AUTOBAHN_DEMO_ROUTER", "ws://127.0.0.1:8080/ws")
    realm = "realm1"
    runner = ApplicationRunner(url, realm)
    runner.run(Component)
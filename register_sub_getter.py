import asyncio
import txaio

txaio.use_asyncio()
from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner
import gamestate


class Component(ApplicationSession):
    async def onJoin(self, details):
        ret = await self.call("wamp.subscription.list")
        for item in ret["exact"]:
            ret = await self.call("wamp.subscription.get", item)
            print(f"Subscriptions: {ret['uri']}")

        ret = await self.call("wamp.registration.list")
        for item in ret["exact"]:
            ret = await self.call("wamp.registration.get", item)
            print(f"Registration: {ret['uri']}")

    def onDisconnect(self):
        asyncio.get_event_loop().stop()


if __name__ == "__main__":
    runner = ApplicationRunner("ws://127.0.0.1:8080/ws", "realm1")
    runner.run(Component)

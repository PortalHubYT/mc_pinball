import asyncio
import txaio

txaio.use_asyncio()
from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner
import gamestate


class Component(ApplicationSession):
    async def onJoin(self, details):
        def signal_emited(*args):
            print(f"o--EMITTED---> {args[0]}")

        await self.register(signal_emited, "call")
        await self.register(signal_emited, "publish")
        await self.register(signal_emited, "register")
        await self.register(signal_emited, "subscribe")

    def onDisconnect(self):
        asyncio.get_event_loop().stop()


if __name__ == "__main__":
    runner = ApplicationRunner("ws://127.0.0.1:8080/ws", "realm1")
    runner.run(Component)

import asyncio
from os import environ
import txaio
import readline
import re

txaio.use_asyncio()
from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner


class Console(ApplicationSession):
    async def onJoin(self, details):
        while True:
            cmd = input()
            if cmd.startswith("call"):
                pass
            else:
                res = re.search(r"^(.*)=(.*)$", cmd)

                if res:
                    key = res.group(1)
                    value = res.group(2)
                    await self.call("edit", key, value)

                self.publish(cmd)


if __name__ == "__main__":
    runner = ApplicationRunner("ws://127.0.0.1:8080/ws", "realm1")
    runner.run(Console)

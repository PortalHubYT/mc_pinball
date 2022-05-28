import asyncio
import sys
from os import environ
import txaio

txaio.use_asyncio()
from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner


import mcapi as mc

verbose = False


class Poster(ApplicationSession):
    async def onJoin(self, details):

        mc.connect("localhost", "test")

        def ping():
            return

        def post(cmd):
            ret = mc.post(cmd)
            if verbose:
                print(cmd)
                if ret != "":
                    print(ret)
            return ret

        await self.register(post, "minecraft.post")
        print("Registered: minecraft.post.")


if __name__ == "__main__":

    args = sys.argv[1:]
    for a in args:
        if a == "-v":
            print("Running poster verbose mode: on")
            verbose = True

    runner = ApplicationRunner("ws://127.0.0.1:8080/ws", "realm1")
    runner.run(Poster)

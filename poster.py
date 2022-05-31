import asyncio
import sys
from os import environ
import txaio

txaio.use_asyncio()
from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner

import mcapi as mc

verbose = False
debug = False


class Poster(ApplicationSession):
    async def onJoin(self, details):

        mc.connect("51.210.255.162", "test")

        def post(cmd):

            ret = mc.post(cmd)
            if verbose:
                print("============COMMAND================")

                if ret != "":
                    if "data get entity" in cmd or "summon" in cmd:
                        if debug is False:
                            print(f"CMD: [/{cmd.split('{')[0][:-1]}]")
                            print(f"RETURN: [{ret.split('{')[0]}]")
                        else:
                            print(f"CMD: [/{cmd}]")
                            print(f"RETURN: [{ret}]")
                    else:
                        print(f"CMD: [/{cmd}]")
                        print(f"RETURN: [{ret}]")
            return ret

        await self.register(post, "minecraft.post")


if __name__ == "__main__":
    args = sys.argv[1:]
    for a in args:
        if a == "-v":
            print("Running poster verbose mode: on")
            verbose = True
        if a == "-vv":
            print("Running poster verbose mode: on")
            verbose = True
            print("Running poster debug mode: on")
            debug = True

    runner = ApplicationRunner("ws://127.0.0.1:8080/ws", "realm1")
    runner.run(Poster)

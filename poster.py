import asyncio
import sys
from os import environ
import txaio

txaio.use_asyncio()
from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner

import mcapi as mc

verbose = False
debug = False


class bcolors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


class Poster(ApplicationSession):
    async def onJoin(self, details):

        mc.connect("51.210.255.162", "test")

        def post(cmd):

            ret = mc.post(cmd)

            start_format = bcolors.OKCYAN
            if "Expected" in ret or "Incorrect" in ret:
                start_format = bcolors.FAIL

            end_format = bcolors.ENDC

            if verbose:
                print("============COMMAND================")

                if ret != "":
                    if "data get entity" in cmd or "summon" in cmd:
                        if debug is False:
                            print(f"CMD: [/{cmd.split('{')[0][:-1]}]")
                            print(
                                f"RETURN: [{start_format}{ret.split('{')[0][:-1]}{end_format}]"
                            )
                        else:
                            print(f"CMD: [/{cmd}]")
                            print(f"[RETURN: [{start_format}{ret}{end_format}]")
                    else:
                        print(f"CMD: [/{cmd}]")
                        print(f"RETURN: [{start_format}{ret}{end_format}]")
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

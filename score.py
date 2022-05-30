import asyncio
import txaio

txaio.use_asyncio()
from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner
import copy
import re
from time import time
from math import floor
import pprint
import pickle


class Component(ApplicationSession):
    async def alives_from_db(self):
        # returns an array with alives uid
        queried_alives = await self.call("data.player.alives")
        return queried_alives

    async def add_alive(self, uid):
        self.alives.append(uid)

    async def onJoin(self, details):
        
        self.alives = await self.alives_from_db()
        await self.check_alive()

        self.subscribe(self.check_alive, "game.tick")
        self.subscribe(self.add_alive, "spawn.new_player")

    async def kill_i(self, i):
        start = time()
        cmd = f"kill @e[tag={i}]"

        await self.call("minecraft.post", cmd)
        updated_data = {
            "last_checked": int(time()),
            "current_alive": 0,
            "alive": 0,
        }
        await self.call("data.player.update", i, updated_data)
        print(f"o---({floor(time() - start)}s)--> Player {i} killed")

    def get_ypos(self, haystack):
        hs = haystack

        pos_start = hs.find("Pos: ")
        hs = hs[pos_start:]
        comma_left = hs.find(",")
        hs = hs[comma_left + 2 :]
        comma_right = hs.find(",")
        hs = hs[: comma_right - 1]

        return int(float(hs))
    
    def get_display_name(self, uid):
        print("uidDDDDD:", uid)
        ret = pickle.loads(self.call('data.player.read', uid))
        return ret['display_name']
        
        

    async def check_alive(self):
        still_alive = await self.call("data.player.alives")
        for i in self.alives:

            cmd = f"data get entity @e[tag={str(i)}, tag=ball, limit=1]"
            ret = await self.call("minecraft.post", cmd)

            if "entity data" in ret:
                y_pos = self.get_ypos(ret)
            else:
                y_pos = None

            # ret.find('the following entity data:')
            # y_pos = re.search(r"^Pos: \[(.*)]$", ret)

            if not isinstance(y_pos, int) or y_pos <= 0:
                await self.kill_i(i)
            else:
                age_in_tick = int(
                    re.search(r"Spigot.ticksLived: ([0-9]*),", ret).group(1)
                )
                age_in_sec = int(age_in_tick / 20)
                print(age_in_sec)
                print(self.get_display_name(uid))

                updated_data = {
                    "last_checked": int(time()),
                    "current_alive": age_in_sec,
                }
                await self.call("data.player.update", i, updated_data)
                still_alive.append(i)

        print(f"o---{len(still_alive)}--> Players alive: {still_alive}")

        self.alives = still_alive

    # def next_round(derp):
    #     cmd = f"execute as @e[tag=[{i}, ball]] at @s run tp @s ~ {self.gamestate.origin_y + self.gamestate.height + 2} ~"
    #         self.call('minecraft.post', cmd)

    def onDisconnect(self):
        asyncio.get_event_loop().stop()


if __name__ == "__main__":
    runner = ApplicationRunner("ws://127.0.0.1:8080/ws", "realm1")
    runner.run(Component)

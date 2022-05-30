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


    async def onJoin(self, details):
        
        self.scores = {}
        await self.check_alive()

        self.subscribe(self.check_alive, "game.tick")

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
    
    async def kill_i(self, i):
        start = time()
        cmd = f"kill @e[tag={i}]"

        await self.call("minecraft.post", cmd)
        self.call("gamestate.alives.remove", i)
        updated_data = {
            "last_checked": int(time()),
            "current_alive": 0,
            "alive": 0,
        }
        await self.call("data.player.update", i, updated_data)
        print(f"o---({floor(time() - start)}s)--> Player {i} killed")
        
    

    async def check_alive(self):
        print("CHECK ALIVE ====================================================")
        alives = await self.call("gamestate.alives.get")
        print(alives)
        for i in alives:

            cmd = f"data get entity @e[tag={str(i)}, tag=ball, limit=1]"
            ret = await self.call("minecraft.post", cmd)
            if "entity data" in ret:
                y_pos = self.get_ypos(ret)
            else:
                y_pos = None

            if not isinstance(y_pos, int) or y_pos <= 0:
                #SHOULD BE KILLED
                await self.kill_i(i)
            else:
                #STAY ALIVE
                if not str(i) in self.scores.keys():
                    self.scores[str(i)] = 1
                else: 
                    self.scores[str(i)] += 1 
                    
                    # updated_data = {
                    #     "last_checked": int(time()),
                    #     "current_alive": age_in_sec,
                    # }
                    # await self.call("data.player.update", i, updated_data)
        self.display_scores()
        
    def display_scores(self):
        print(self.scores)
        # top_ten = sorted_dict
        # print(top_ten)
        
    def delete_score(self, uid):

        self.call('minecraft.post', f"scoreboard players set {uid['tag'][:10]} alive_for 0")
        self.call('minecraft.post', f"scoreboard players reset {uid['tag'][:10]} alive_for")

        if "PortalHub" in uid["tag"]:
            return
        with open("db/high_score", "r") as f:
            current_highest = f.read()

        if uid["time"] > int(current_highest):
            with open("db/high_score", "w") as f:
                f.write(str(uid["time"]))

                self.call('minecraft.post', 
                    f"bossbar set minecraft:peglin name \"High score: {uid['time']} | {uid['name']}\""
                )

        self.call('minecraft.post', 
            f"title funyrom actionbar \"{uid['name']} died after {uid['time']} seconds\""
        )
        
    
    def display_score(self, top_scores):

        for score in top_scores:

            cmd = (
                f"data merge entity @e[type={ball['mob_type']},tag={ball['tag']},limit=1]"
                + " {Glowing:0b}"
            )
            self.call('minecraft.post', cmd)

            if not "PortalHub" in ball["tag"]:
                self.call('minecraft.post', 
                    f"scoreboard players set {ball['tag'][:10]} alive_for {ball['time']}"
                )

        cmd = (
            f"data merge entity @e[type={balls[-1]['mob_type']},tag={balls[-1]['tag']},limit=1]"
            + " {Glowing:1b}"
        )
        self.call('minecraft.post', cmd)
            
                

    # def next_round(derp):
    #     cmd = f"execute as @e[tag=[{i}, ball]] at @s run tp @s ~ {self.gamestate.origin_y + self.gamestate.height + 2} ~"
    #         self.call('minecraft.post', cmd)

    def onDisconnect(self):
        asyncio.get_event_loop().stop()


if __name__ == "__main__":
    runner = ApplicationRunner("ws://127.0.0.1:8080/ws", "realm1")
    runner.run(Component)

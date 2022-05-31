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


SCOREBOARD_WIDTH = 10

class Component(ApplicationSession):

    def reset_scores(self):
        scores = {}
        for uid in self.names:
            scores[uid] = 0
        return scores
    
    async def onJoin(self, details):
        self.names = await self.call('gamestate.names.all')
        self.scores = self.reset_scores()
        
        await self.check_alive()
        # with open("db/high_score", "r") as f:
        #         self.highscore = f.read()
        

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
    
    async def kill(self, uid, name):
        start = time()
        cmd = f"kill @e[tag={uid}, type=!player]"

        await self.call("minecraft.post", cmd)
        
        updated_data = {
            "last_checked": int(time()),
            "current_alive": 0,
            "alive": 0,
        }
        self.delete_score(uid, name)
        self.call("gamestate.names.remove", uid)
        self.names.pop(str(uid))
        self.scores.pop(str(uid))
        self.call('minecraft.post', f'scoreboard players reset {name} alive_for')
        await self.call("data.player.update", uid, updated_data)
        print(f"o-({floor(time() - start)}s)-> Player {uid} killed")
        
    

    async def check_alive(self):
        self.names = await self.call('gamestate.names.all')
        print(f"o--> Check alive on {len(self.names)} players")
        
        
        names_copy = self.names.copy()
        # print(names_copy)
        for i in names_copy:
            i = int(i)
            cmd = f"data get entity @e[tag={str(i)}, tag=ball, limit=1]"
            ret = await self.call("minecraft.post", cmd)
            if "entity data" in ret:
                y_pos = self.get_ypos(ret)
            else:
                y_pos = None

            if not isinstance(y_pos, int) or y_pos <= 0:
                #SHOULD BE KILLED
                
                await self.kill(i, names_copy[str(i)])
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
        await self.display_scores(names_copy)
    
    async def display_scores(self, names):
        
        # print("unsorted:", self.scores)
        top_ten = sorted(self.scores.items(), key=lambda item: item[1], reverse=True)[:10]
        
        for entry in top_ten:
            # print("namees here: ", self.names)
            tag = entry[0]
            name = names[tag]
        
            
            # print(name, tag)
            # cmd = (
            #     f"data merge entity @e[type={ball['mob_type']},tag={ball['tag']},limit=1]"
            #     + " {Glowing:0b}"
            # )
            # self.call('minecraft.post', cmd)

            if not "PortalHub" in name:
                ret = await self.call('minecraft.post', 
                    f"scoreboard players set {name[:SCOREBOARD_WIDTH]} alive_for {self.scores[tag]}"
                )
                # print("SCORE: ", ret)

        # cmd = (
        #     f"data merge entity @e[type={balls[-1]['mob_type']},tag={balls[-1]['tag']},limit=1]"
        #     + " {Glowing:1b}"
        # )
        # self.call('minecraft.post', cmd)
            
                

    # def next_round(derp):
    #     cmd = f"execute as @e[tag=[{i}, ball]] at @s run tp @s ~ {self.gamestate.origin_y + self.gamestate.height + 2} ~"
    #         self.call('minecraft.post', cmd)
    def delete_score(self, uid, name):
        self.call('minecraft.post', f"scoreboard players set {name[:SCOREBOARD_WIDTH]} alive_for 0")
        self.call('minecraft.post', f"scoreboard players reset {name[:SCOREBOARD_WIDTH]} alive_for")
        
        # if self.names[str(uid)] > self.highscore:
        #     with open("db/high_score", "w") as f:
        #         f.write(str(self.scores[str(uid)]))
            
        #     with open("db/high_score", "w") as f:
        #         f.write(str(self.scores[str(uid)]))

        # self.call('minecraft.post', 
        #         f"bossbar set minecraft:peglin name \"High score: {uid['time']} | {uid['name']}\""
        # )

        # print("scores=", self.scores)
        self.call('minecraft.post', 
            f"title funyrom actionbar \"{name} died after {self.scores[str(uid)]} seconds\""
        )

    def onDisconnect(self):
        for uid in self.scores:
            self.delete_score(uid, self.names[uid])
        asyncio.get_event_loop().stop()


if __name__ == "__main__":
    runner = ApplicationRunner("ws://127.0.0.1:8080/ws", "realm1")
    runner.run(Component)

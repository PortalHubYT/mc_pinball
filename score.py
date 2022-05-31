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
import random


SCOREBOARD_WIDTH = 10

class Component(ApplicationSession):
    def reset_scores(self):
        scores = {}
        for uid in self.names:
            scores[uid] = 0
        return scores
    
    async def onJoin(self, details):
        self.highscore = await self.call('gamestate.highscore.get')
        self.call('minecraft.post', 
                    f"bossbar set minecraft:peglin name \"High score: {self.highscore}\""
            )
        self.names = await self.call('gamestate.names.all')
        self.gamestate = await self.call('gamestate.get')
        self.scores = self.reset_scores()
        
        await self.check_alive()
        
        self.register(self.reset_scores,'score.reset')
        self.subscribe(self.check_alive, "game.tick")

    
    
    async def kill(self, uid, name):
        cmd = f"kill @e[tag={uid}, type=!player]"

        await self.call("minecraft.post", cmd)
        
        updated_data = {
            "last_checked": int(time()),
            "current_alive": 0,
            "alive": 0,
            # "score": 
        }
        
        self.delete_player(uid, name)
        await self.call("gamestate.names.remove", uid)
        
        if not str(uid) in self.names:
            return print(f"/!\ Tried to pop fromm names with id {uid}: no such key")
        else:
            self.names.pop(str(uid), None)
        
        if not str(uid) in self.scores:
            return print(f"/$\ Tried to pop fromm scores with id {uid}: no such key")
        else:
            self.scores.pop(str(uid), None)
        
       
        
        self.call('minecraft.post', f'scoreboard players reset {name} alive_for')
        await self.call("data.player.update", uid, updated_data)
        
    
    def get_pos(self, haystack):
        hs = haystack

        pos_start = hs.find("Pos: ")
        
        hs = str(hs[pos_start:])
        hsold = hs
        hs = hs[hs.find("[")+1:hs.find("]")]
        hs = hs.split(', ')
        
        ret = (int(float(hs[0][:-1])), int(float(hs[1][:-1])), int(float(hs[2][:-1])))
        return (ret)
        
    
    async def check_alive(self):
        
        # await self.call('minecraft.post', f"execute as @e[tag=ball,x={self.gamestate['origin_x']},y={self.gamestate['origin_y']},z={self.gamestate['origin_z']},dx={self.gamestate['depth']},dz={int(self.gamestate['width'] / 3)},dy=-10] at @s run tp @s ~ ~{self.gamestate['height'] - 3} ~")
        # await self.call('minecraft.post', f"execute as @e[tag=ball,x={self.gamestate['origin_x']},y={self.gamestate['origin_y']},z={self.gamestate['origin_z']},dx={self.gamestate['depth']},dz={int(self.gamestate['width'] / 3)},dy=-10] at @s run tp @s ~ ~{self.gamestate['height'] - 3} ~")
        # await self.call('minecraft.post', f"execute as @e[tag=ball,x={self.gamestate['origin_x']},y={self.gamestate['origin_y']},z={self.gamestate['origin_z']},dx={self.gamestate['depth']},dz={int(self.gamestate['width'] / 3)},dy=-10] at @s run tp @s ~ ~{self.gamestate['height'] - 3} ~")
        
        self.names = await self.call('gamestate.names.all')
        print(f"\no--> Check alive on {len(self.names)} players")
        
        
        
        
        
        
        
        names_copy = self.names.copy()
        # print(names_copy)
        for i in names_copy:
            i = int(i)
            cmd = f"data get entity @e[tag={str(i)}, tag=ball, limit=1]"
            ret = await self.call("minecraft.post", cmd)
            if "entity data" in ret:
                x_pos, y_pos, z_pos = self.get_pos(ret)
            else:
                x_pos, y_pos, z_pos = (None,  None, None)

            # print(x_pos, y_pos, z_pos)
            
            
            if not isinstance(y_pos, int):
                await self.kill(i, names_copy[str(i)])
            else:
                if y_pos <= 5:
                    if z_pos - self.gamestate['origin_z'] <= int(self.gamestate['width'] / 5):
                        print(f"respawning le pote: {i} {names_copy[str(i)]}, z= {z_pos}")
                        self.call('minecraft.post', f"execute as @e[tag=ball, tag={i}] at @s run tp {(self.gamestate['origin_x'] + self.gamestate['depth']) / 2} ~{self.gamestate['height'] + self.gamestate['origin_y'] - 2} {random.randrange(self.gamestate['origin_z'], self.gamestate['width'])}")
                    # elif x_pos <= self.gamestate['origin_x'] <= 2 * int(self.gamestate['width'] / 3):
                        # print("kill le pote: {i} {names_copy[str(i)]}")
                        # await self.kill(i, names_copy[str(i)])
                    else:
                        print(f"x2 le pote le pote: {i} {names_copy[str(i)]}")
                        await self.kill(i, names_copy[str(i)])
                        pass
                        
                        
                #respawn bucket
                
                
                
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
        top_ten = sorted(self.scores.items(), key=lambda item: item[1], reverse=True)[:10]
        current_glowing = 0
        for entry in top_ten:
            tag = entry[0]
            # print(f"{tag=}")
            if tag not in names:
                data = pickle.loads(await self.call('data.player.read', tag))
                name = data['display_name']
                # self.delete_player(tag, name)
                print(f"[[[[[[name was on {tag} , it's now: {name}]]]]]]]")
                return
                
            else:
                name = names[tag]

            if not "PortalHub" in name and not "Nightbot" in name:
                ret = await self.call('minecraft.post', 
                    f"scoreboard players set {name[:SCOREBOARD_WIDTH]} alive_for {self.scores[tag]}"
                )
                
        cmd = (
            f"data merge entity @e[type=slime,tag={current_glowing},limit=1]"
            + " {Glowing:0b}"
        )
        self.call('minecraft.post', cmd)
        if len(top_ten):
            current_glowing = top_ten[0][0]
        cmd = (
            f"data merge entity @e[type=slime,tag={current_glowing},limit=1]"
            + " {Glowing:1b}"
        )
        self.call('minecraft.post', cmd)


    def delete_player(self, uid, name):
        # self.call('minecraft.post', f"scoreboard players set {name[:SCOREBOARD_WIDTH]} alive_for 0")
        self.call('minecraft.post', f"scoreboard players reset {name[:SCOREBOARD_WIDTH]} alive_for")
        
        if str(uid) not in self.scores:
            return print(f"/!\ Tried to kill an id {uid} not in scores")
        score = self.scores[str(uid)]
        
        if score > self.highscore:
            self.highscore = score
            self.call('gamestate.highscore', score)
            self.call('minecraft.post', 
                    f"bossbar set minecraft:peglin name \"High score: {score} | {name}\""
            )

        self.call('minecraft.post', 
            f"title funyrom actionbar \"{name} died after {self.scores[str(uid)]} seconds\""
        )
        # player_update_id[]

    def onDisconnect(self):
        for uid in self.scores:
            self.delete_player(uid, self.names[uid])
        asyncio.get_event_loop().stop()


if __name__ == "__main__":
    runner = ApplicationRunner("ws://127.0.0.1:8080/ws", "realm1")
    runner.run(Component)

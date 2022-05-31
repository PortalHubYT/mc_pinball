import asyncio
import txaio
txaio.use_asyncio()
from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner

import pickle

color_list = [
 'minecraft:white_concrete',
 'minecraft:orange_concrete',
 'minecraft:magenta_concrete',
 'minecraft:light_blue_concrete',
 'minecraft:yellow_concrete',
 'minecraft:lime_concrete',
 'minecraft:pink_concrete',
 'minecraft:gray_concrete',
 'minecraft:light_gray_concrete',
 'minecraft:cyan_concrete',
 'minecraft:purple_concrete',
 'minecraft:blue_concrete',
 'minecraft:brown_concrete',
 'minecraft:green_concrete',
 'minecraft:red_concrete',
 'minecraft:black_concrete',
]

class Component(ApplicationSession):

    async def onJoin(self, details):
        self.gs = await self.call('gamestate.get')
        self.subscribe(self.on_message, 'chat.message')
        
    def on_message(self, message):
        message = pickle.loads(message)
        true_message = "".join(
                    s for s in message["messageEx"] if isinstance(s, str))
        if true_message.startswith('color'):
            
            args = true_message.split(' ')
            
            try:
                input_color = str(args[1])
                z = int(args[2])
                y = int(args[3])
            except:
                return print(f"wrong input: {args}")
                
            
            for c, color in enumerate(color_list):
                if input_color.lower() in str(color):
                    block = color_list[c]
                    if z <= self.gs['origin_z'] + self.gs['width'] and z >= self.gs['origin_z']:
                        if y <= self.gs['origin_y'] + self.gs['height'] and z >= self.gs['origin_y']:
                            
                            cmd = f"setblock {self.gs['depth'] + 1} {y} {z} {block}"
                            print("calling:", cmd)
                            self.call('minecraft.post', cmd)
                    
                    
            
            
            
                
                    
        

    def onDisconnect(self):
        
        asyncio.get_event_loop().stop()

if __name__ == '__main__':
    runner = ApplicationRunner("ws://127.0.0.1:8080/ws", "realm1")
    runner.run(Component)
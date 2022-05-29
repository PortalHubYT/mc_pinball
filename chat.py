import asyncio
import sys
import signal 
from os import environ
import txaio
txaio.use_asyncio()
from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner
from autobahn.wamp import ApplicationError
import pytchat
import pickle
import json

from input import sanitize_very_strict



        
class Chat(ApplicationSession):
    def __init__(self, *args):
        super().__init__(*args)
        self.call = self.custom_call
        
    async def custom_call(self, *args):
        super().call(*args)
        # try:
        #     super().call(*args)
        # except ApplicationError as e:
        #     print(e)
            
    async def spawn_from_message(self, message):
        # id = await self.call('ensure_player_exists', )
        player_data ={
                    "display_name": sanitize_very_strict(message['author']['name']),
                    "username": message['author']['name'],
                    "alive": 1,
                    "current_alive":0,
                    # "best_alive": "INTEGER",
                    "last_checked": message['timestamp'],
                    "channel_id": message['author']['channelId'],
                }
        try:
            id = await self.call("data.create_player", player_data)
        except Exception as e:
            print(f"    (ERROR): data.create_player failed for {player_data['username']}")
        try:
            
            await self.call("spawn.slime.random", id, player_data)
        except Exception as e:
            print(f"     (ERROR): spawn.slime.random failed with {e}")
        return id
            
    async def onJoin(self, details):
        self.stream_id = "5qap5aO4i9A"
        self.stream_url = f"https://www.youtube.com/watch?v={self.stream_id}"
        
        chat = pytchat.create(video_id=self.stream_url,interruptable=False, hold_exception=False)
        
        
        
        while chat.is_alive():
            for c in chat.get().sync_items():
                message = json.loads(c.json())
                
                print("=====MESSAGE================")
                name = message['author']['name']
                text = "".join(s for s in message['messageEx'] if isinstance(s, str))
                print(f"[{name}]: {text}")
                print("============================")
                
                id = await self.call('data.player.exist', message['author']['channelId'])
                
                await self.spawn_from_message(message)
                
        

if __name__ == '__main__':
    runner = ApplicationRunner("ws://127.0.0.1:8080/ws", "realm1")
    runner.run(Chat)
import asyncio
import sys
import signal 
from os import environ
import txaio
txaio.use_asyncio()
from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner
import pytchat
import pickle

from input import sanitize_very_strict


        
class Chat(ApplicationSession):
    

    def spawn_from_message(message):
            
            pass
        
    async def board_changed(self):
            self.board = pickle.loads(await self.call("board.get"))
            print(self.board)
            print(type(self.board))
            
            
    async def onJoin(self, details):
        # resp = await self.call("board.get")
        # self.board = pickle.loads(resp)
        
                
        stream_id = "5qap5aO4i9A"
        stream_url = f"https://www.youtube.com/watch?v={stream_id}"
        chat = pytchat.create(video_id=stream_url,interruptable=False, hold_exception=False)
                    
        while chat.is_alive():
            for c in chat.get().sync_items():
                message = c.json()
        

if __name__ == '__main__':
    runner = ApplicationRunner("ws://127.0.0.1:8080/ws", "realm1")
    runner.run(Chat)
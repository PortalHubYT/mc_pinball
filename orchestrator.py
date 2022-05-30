from nturl2path import url2pathname
import txaio
txaio.use_asyncio()
from autobahn.asyncio.component import Component
from autobahn.asyncio.wamp import ApplicationRunner
import asyncio


from builder import Builder
from chat import Chat
from console import Console
from database import Database
from gamestate import GameState
from poster import Poster
from scheduler import Scheduler
from spawner import Spawner
# from score import Score

clock = Component(
    transports=u"ws://localhost:8080/ws",
    realm=u"realm1",
 )



to_load = [Builder, Chat, Console, Database, GameState, Poster, Scheduler,Spawner]

if __name__ == "__main__":
    url = "ws://127.0.0.1:8080/ws"
    realm = "realm1"
    
    
    runners = []
    coros = []
    for i, comp in enumerate(to_load):
        print(f"Loading:{('.' * (i % 3)).ljust(3)}" + f" {comp}")
        runner = ApplicationRunner(url, realm)
        runners.append(runner)
        
        coro = runner.run(comp, start_loop=False)
        coros.append(coro)
        asyncio.get_event_loop().run_until_complete(coro)
    

    asyncio.get_event_loop().run_forever()

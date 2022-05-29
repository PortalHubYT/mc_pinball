
import pickle 
import asyncio
import default_gamestate
       
from pyats.datastructures import AttrDict
 
class GameState(object):
    
    def __init__(self, client):
        self._publish = client.publish
        self._state = AttrDict()
        client.publish('gamestate.sync_needed', None)
            
        client.subscribe(self.sync, "gamestate.sync")
        
        
    def __str__(self):
        return self.__repr__()
    def __repr__(self):
        return self._state.__repr__()
    
    
    def __setitem__(self, k, v):
        self._state[k] = v
        self._publish("gamestate.sync_needed", self._state)
        self._publish(f"gamestate.{k}", v)
        
    def __setattr__(self, k, v):
        if k == "_state" or k == "_publish":
            super().__setattr__(k, v)
        else:
            self._state[k] = v
            self._publish("gamestate.sync_needed", self._state)
            self._publish(f"gamestate.{k}", v)
            
    def __getattr__(self, k):
        return self._state[k]
    def __getitem__(self, k):
        return self._state[k]
            
    def sync(self, new_state):
        # print(f"sync:\n{str(self._state).ljust(20)}    ->>   {new_state}")
        super().__setattr__('_state', AttrDict(new_state))
        
        
async def create(client):
    new_instance = GameState(client)
    ready = False
    while not ready:
        if new_instance._state:
            ready = True
        await asyncio.sleep(0.001)
    return new_instance
    
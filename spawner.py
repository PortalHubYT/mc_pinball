
from typing import Dict


def spawn_slime():
    
    ret = await self.call('board.get', )
    




def get_slime_nbt():
    nbt = mc.NBT(
        {
            "Size": 1,
            "Tags": [f"{final_name}"],
            "Passengers": [
                {
                    "id": "minecraft:area_effect_cloud",
                    "Tags": [f"{final_name}"],
                    "Particle": "block air",
                    "Duration": 120000,
                    "Passengers": [
                        {
                            "id": "minecraft:area_effect_cloud",
                            "Particle": "block air",
                            "Tags": [f"{final_name}"],
                            "Duration": 120000,
                            "Passengers": [
                                {
                                    "id": "minecraft:area_effect_cloud",
                                    "Particle": "block air",
                                    "Tags": [f"{final_name}"],
                                    "Duration": 120000,
                                    "CustomNameVisible": 1,
                                    "CustomName": '{ "text": "'
                                    + f"{final_name}"
                                    + '"}',
                                }
                            ],
                        }
                    ],
                }
            ],
            "ActiveEffects": [
                {"Id": 2, "Amplifier": 255, "Duration": 999999, "ShowParticles": 0},
                {"Id": 11, "Amplifier": 5, "Duration": 999999, "ShowParticles": 0},
                {
                    "Id": 28,
                    "Amplifier": 255,
                    "Duration": 999999 if env["slow_falling"] else 0,
                    "ShowParticles": 0,
                },
            ],
        }
    )
    
def spawn_player(self, tag="empty_tag"):
            
            cmd = f"{}"
            self.call('minecraft.post', )
    
    
    
    
    
    
    
    
    # self.origin
    # self.layout_2d= [
    #     [Nothing, Peg, ],
    #     [Nothing, Peg, ],
    #     [Nothing, Peg, ],
    # ]
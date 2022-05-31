import asyncio
from os import environ
import txaio

txaio.use_asyncio()
from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner
import mcapi as mc
import random
from input import sanitize_very_strict, sanitize_less_strict
import pickle

NAME_WIDTH = 50

class Spawner(ApplicationSession):
    async def onJoin(self, details):
        self.gs = await self.call("gamestate.get")

        def get_random_spawning_point():
            x = random.randrange(0, self.gs["width"] - 1)
            y = random.randrange(int(self.gs["height"] * 0.7), self.gs["height"])
            return (x, y)

        def translate_coords(x, y):
            return f"{(self.gs['origin_x'] + self.gs['depth']) / 2} {y + self.gs['origin_y'] + 3} {x + self.gs['origin_z']}"

        async def spawn_slime(x, y, tag, display_name="dummy", mob_type="minecraft:slime"):
            nbt = self.get_slime_nbt(display_name, tag)
            coords = translate_coords(x, y)
            cmd = f"summon {mob_type} {coords} {nbt}"
            ret = await self.call("minecraft.post", cmd)


        async def spawn_slime_random(tag, display_name="dummy", mob_type="minecraft:slime"):
            x, y = get_random_spawning_point()
            await spawn_slime(x, y, tag, display_name, mob_type)

        async def spawn_player_from_message(message):
            message = pickle.loads(message)
            player_data = {
                "display_name": sanitize_less_strict(f'[{message["author"]["name"]}]: ' + "".join(
                        s for s in message["messageEx"] if isinstance(s, str)
                    )[:20]),
                "username": message["author"]["name"],
                "alive": 1,
                "current_alive": 0,
                "last_checked": message["timestamp"],
                "channel_id": message["author"]["channelId"],
            }

            uid = await self.call("data.player.ensure_exists", player_data)

            names = await self.call("gamestate.names.all")
            if not uid in names.keys():
                self.publish("spawn.player.new", [uid, sanitize_very_strict(player_data["display_name"])])
                if message["author"]["isChatSponsor"] or message["author"]["isChatOwner"]:
                    mob_type = "magma_cube"
                else:
                    mob_type = "slime"
                await spawn_slime_random(uid, player_data["display_name"], mob_type)
                print(
                    f"o--> ({player_data['display_name'][:15]}) [id: {uid}] spawned from message"
                )
                
        await self.register(spawn_slime, "spawn.slime.place")
        await self.register(spawn_slime_random, "spawn.slime.random")
        await self.subscribe(spawn_player_from_message, "chat.message")

    def onDisconnect(self):
        asyncio.get_event_loop().stop()

    def get_slime_nbt(self, name, tag):

        tag = str(tag)
        nbt = mc.NBT(
            {
                "Size": 1,
                "Tags": [tag, "ball"],
                "Passengers": [
                    {
                        "id": "minecraft:area_effect_cloud",
                        "Tags": [tag],
                        "Particle": "block air",
                        "Duration": 120000,
                        "Passengers": [
                            {
                                "id": "minecraft:area_effect_cloud",
                                "Particle": "block air",
                                "Tags": [tag],
                                "Duration": 120000,
                                "Passengers": [
                                    {
                                        "id": "minecraft:area_effect_cloud",
                                        "Particle": "block air",
                                        "Tags": [tag],
                                        "Duration": 120000,
                                        "CustomNameVisible": 1,
                                        "CustomName": '{ "text": "'
                                        + f"{name[:NAME_WIDTH]}"
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
                        # "Duration": 999999 if self.gs.slow_falling else 0,
                        "Duration": 999999,
                        "ShowParticles": 0,
                    },
                ],
            }
        )
        return nbt


if __name__ == "__main__":
    runner = ApplicationRunner("ws://127.0.0.1:8080/ws", "realm1")
    runner.run(Spawner)

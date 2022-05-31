import asyncio
import txaio

txaio.use_asyncio()
import os
import pickle
from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner
import default_gamestate


class GameState(ApplicationSession):
    async def onJoin(self, details):

        self.highscore = self.load_highscore()
        if self.highscore == None:
            self.highscore = 0
        self.names = {}
        self.alives = self.load_alives()
        if self.alives == None:
            self.alives = []
        else:
            for uid in self.alives:
                player_data = pickle.loads(await self.call("data.player.read", uid))
                if player_data:
                    self.names[str(uid)] = player_data["display_name"]

        self.gamestate = self.load_gamestate()
        if self.gamestate == None:
            self.gamestate = default_gamestate.default

        default_env_commands = [
            f"region flag -w world __global__ tnt deny",
            f"whitelist on",
            f"time set noon",
            f"gamerule sendCommandFeedback false",
            f'title @e[type=player] title "Restarting..."',
            f'title @e[type=player] subtitle "Type anything to join the game"',
            f'scoreboard objectives add a dummy "Longest alive"',
            f'scoreboard objectives add a dummy "Highest scores"',
            f"scoreboard objectives setdisplay sidebar alive_for",
            f"scoreboard players reset * alive_for",
            f'scoreboard objectives add alive_for dummy "Alive"',
            f'bossbar add minecraft:peglin "default"',
            f'bossbar set minecraft:peglin name "High score: {0}"',
            f"bossbar set minecraft:peglin visible true",
            f"bossbar set minecraft:peglin players @a",
            f"bossbar set minecraft:peglin style progress",
        ]

        for cmd in default_env_commands:
            await self.call("minecraft.post", cmd)

        self.to_save = ["alives", "gamestate", "names"]

        self.register(self.get_alives, "gamestate.alives.get")  # returns alives list
        self.register(
            self.add_alive, "gamestate.alives.add"
        )  # adds an id in alives list
        self.register(
            self.remove_alive, "gamestate.alives.remove"
        )  # adds an id in alives list
        self.register(
            self.remove_alive_all, "gamestate.alives.remove_all"
        )  # adds an id in alives list
        self.register(self.get_gamestate, "gamestate.get")  # returns gamestate dict
        self.register(
            self.get_gamestate_key, "gamestate.get.key"
        )  # get value for gamestate[key]
        self.register(
            self.update_gamestate, "gamestate.update"
        )  # replace gamestate dict
        self.register(
            self.update_gamestate_key, "gamestate.update.key"
        )  # get value for gamestate[key]

        self.register(self.set_highscore, "gamestate.highscore.set")
        self.register(self.get_highscore, "gamestate.highscore.get")

        self.register(self.add_name, "gamestate.names.add")
        self.register(self.get_names, "gamestate.names.all")
        self.register(self.get_name, "gamestate.names.get")
        self.register(self.remove_name, "gamestate.names.remove")
        self.register(self.remove_all_names, "gamestate.names.remove_all")
        self.register(self.remove_all, "gamestate.remove_all")
        self.subscribe(self.add_alive, "spawn.player.new")

    def load_highscore(self):
        return self.load_from_file("db", "highscore")

    def set_highscore(self, value):
        self.highscore = value

    def get_highscore(self):
        return self.highscore

    def remove_all(self):
        self.remove_all_names()
        self.names = {}

    def ensure_file(self, dir, store_name):
        filepath = f"{dir}/{store_name}"
        if not os.path.exists(f"{dir}"):
            os.mkdir(dir)
        if not os.path.exists(filepath):
            open(filepath, "w+").close()

    def load_alives(self):
        return self.load_from_file("db", "alives")

    def load_gamestate(self):
        return self.load_from_file("db", "gamestate")

    def load_from_file(self, dir, store_name):
        self.ensure_file(dir, store_name)
        with open(f"{dir}/{store_name}", "rb") as f:
            try:
                data = pickle.load(f)
            except EOFError:
                print("Empty store")
                data = None
        return data

    def store_to_file(self, store_name):
        data = getattr(self, store_name)
        with open(f"db/{store_name}", "wb") as f:
            pickle.dump(data, f)

    def get_alives(self):
        return self.alives

    def add_alive(self, data):

        uid = data[0]
        name = data[1]
        print(f"o--> Adding {uid} {name} to alives and names")
        self.alives.append(uid)
        self.names[str(uid)] = name

    def remove_alive(self, uid):
        print(f"o--> Removing {uid} from alives")
        self.alives.remove(uid)

    def remove_alive_all(self):

        self.alives = []

    def get_names(self):
        pickle.dumps(self.names)
        return self.names

    def get_name(self, uid):
        return self.names[uid]

    def add_name(self, uid, name):
        self.names[str(uid)] = name

    def remove_name(self, uid):
        self.names.pop(str(uid), None)

    def remove_all_names(self):
        self.names = {}

    def get_gamestate(self):
        return self.gamestate

    def get_gamestate_key(self, key):
        return self.gamestate[key]

    def update_gamestate(self, new_gamestate):
        self.gamestate = new_gamestate
        self.publish("gamestate.changed")

    def update_gamestate_key(self, k, v):
        self.gamestate[k] = v
        self.publish("gamestate.changed")

    async def onDisconnect(self):
        for store_name in self.to_save:
            print(f"o-> Saving {store_name} to file")
            self.store_to_file(store_name)
        asyncio.get_event_loop().stop()


if __name__ == "__main__":
    runner = ApplicationRunner("ws://127.0.0.1:8080/ws", "realm1")
    runner.run(GameState)

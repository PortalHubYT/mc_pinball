import sys
import asyncio
import os
import txaio

txaio.use_asyncio()
from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner

import datetime
import json
import sqlite3
import time
from pyats.datastructures import AttrDict
from sqlite3 import Error

GAMESTATE = 1

import pickle
from time import time
from math import floor


class Database(ApplicationSession):
    async def onJoin(self, details):
        self.name = "pinball"
        self.conn = self.create_connection()
        self.cursor = self.conn.cursor()
        self.execute = self.cursor.execute
        self.tables = {
            "players": {
                "types": {
                    "id": "INTEGER PRIMARY KEY",
                    "display_name": "TEXT",
                    "username": "TEXT",
                    "alive": "INTEGER",
                    "current_alive": "INTEGER",
                    "best_alive": "INTEGER",
                    "last_checked": "INTEGER",
                    "channel_id": "TEXT",
                },
                "schema": None,
            },
            "gamestates": {
                "types": {
                    "id": "INTEGER PRIMARY KEY",
                    "blob": "BLOB",
                    "timestamp": "INTEGER",
                },
                "schema": None,
            },
        }

        for table in self.tables:
            self.tables[table]["schema"] = [
                field for field in self.tables[table]["types"]
            ]
            self.ensure_table(table)

        await self.register(self.create_player, "data.create_player")
        await self.register(self.player_read_id, "data.player.read")
        await self.register(self.player_update_id, "data.player.update")
        await self.register(self.player_delete_id, "data.player.delete")
        await self.register(self.ensure_player_exist, "data.player.ensure_exists")
        await self.register(self.player_reset_all, "data.player.reset")

    # async def onDisconnect(self):
    #     return super().onDisconnect()

    ####################################
    ##            PLAYERS             ##
    ##                                ##
    ####################################

    def player_read_channelid(self, channelid):
        start = time()
        cmd = f"SELECT id FROM 'players' WHERE channel_id = '{channelid}';"
        id = self.execute(cmd).fetchone()
        print(
            f"o---({floor(time()- start)}s)---> Reading player with channelid {channelid}"
        )
        if isinstance(id, tuple):
            return id[0]
        else:
            return None

    def ensure_player_exist(self, player_data):
        id = self.player_read_channelid(player_data["channel_id"])

        if not id:
            id = self.create_player(player_data)

        if isinstance(id, list):
            return id[0]
        else:
            return id

    def player_read_id(self, id):
        data = self.read_id(id, "players")
        print(data)
        ser_data = pickle.dumps(data)
        return ser_data

    def print_table(self, table="players"):
        cmd = f"SELECT * FROM {table}"
        ret = self.execute(cmd).fetchall()
        for entry in ret:
            print(entry)

    def player_reset_all(self):
        cmd = f"DROP TABLE players"
        self.execute(cmd)

    def player_delete_id(self, id):
        cmd = f"DELETE FROM players WHERE id = {id};"
        self.execute(cmd)
        self.conn.commit()

    def create_player(self, data={"username": "dummy"}):
        start = time()
        if "username" not in data:
            return print("Invalid create_user: no username")
        fields = []
        values = []
        for field in data:
            fields.append(field)
            values.append(str(data[field]))

        formated_fields = f"({', '.join(fields)})"
        formated_values = f"({', '.join([v.__repr__() for v in values])})"

        if not data:
            formated_fields = ""
            formated_values = ""

        cmd = f"INSERT INTO players {formated_fields} VALUES {formated_values};"
        id = self.execute(cmd).lastrowid
        self.conn.commit()

        print(f"o---({floor(time() - start)}s)---> Creating player with id {id}")
        return id

    def player_update_id(self, id, data):
        start = time()
        for item in data:
            if isinstance(data[item], str):
                value = f"'{data[item]}'"
            else:
                value = data[item]
            cmd = f"UPDATE players SET {item} = {value} WHERE id = {id};"
            self.execute(cmd)
        self.conn.commit()
        print(
            f"o---({floor(time() - start)}s)---> Updated player {id} with data:\n{data}"
        )

    ####################################
    ##              MISC             ##
    ##                                ##
    ####################################
    def read_id(self, id, table):
        start = time()
        data = {}
        cmd = f"SELECT {', '.join(self.tables[table]['schema'])} FROM {table} WHERE id = {id}"

        cursor = self.execute(cmd)
        for item in cursor:
            for i, field in enumerate(item):
                data[self.tables[table]["schema"][i]] = field

        print(f"o---({floor(time() - start)}s)---> Reading {table} with id {id}")
        return data

    def ensure_table(self, table):
        cmd = f"PRAGMA table_info({table})"
        current_table = self.execute(cmd).fetchall()

        if not current_table:
            self.create_table(table)

        current_table_fields = [field[1] for field in current_table]

        for field in self.tables[table]["schema"]:
            if field not in current_table_fields:
                cmd = f"ALTER TABLE {table} ADD COLUMN {field}"
                self.execute(cmd)

    def create_table(self, table):
        formated_types = "("
        for type in self.tables[table]["types"]:

            formated_types = (
                f"{formated_types}{type} {self.tables[table]['types'][type]}, "
            )
        formated_types = formated_types[:-2] + ")"

        cmd = f"CREATE TABLE {table} {formated_types};"
        self.execute(cmd)

    def create_connection(self):
        if not os.path.exists("db"):
            os.makedirs("db")
        try:
            return sqlite3.connect(f"db/{self.name}.db")
        except Error as e:
            print("Failed to connect to database: ", e)


if __name__ == "__main__":
    runner = ApplicationRunner("ws://127.0.0.1:8080/ws", "realm1")
    runner.run(Database)

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

class Database(ApplicationSession):
    async def onJoin(self, details):
        self.name = "pinball"
        self.conn = self.create_connection()
        self.cursor = self.conn.cursor()
        self.execute = self.cursor.execute
        self.tables = {
            "players": {
                "types": {
                    # "id": "INTEGER PRIMARY KEY",
                    "display_name": "TEXT",
                    "username": "TEXT",
                    "alive": "INTEGER",
                    "current_alive":"INTEGER",
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
            }
        }
        
        for table in self.tables:
            self.tables[table]["schema"] = [ field for field in self.tables[table]['types']]
            self.ensure_table(table)
        
        await self.register(self.player_reset_all, "data.delete_everything")
        await self.register(self.create_player, "data.create_player")
        await self.register(self.player_read_id, "data.player_read_id")
        await self.register(self.player_update_id, "data.update_id")
        await self.register(self.player_delete_id, "data.delete_id")
        
        await self.subscribe(self.gamestate_sync_needed, "gamestate.sync_needed")
        
    ####################################
    ##           GAMESTATE            ##
    ##                                ##
    ####################################
    def gamestate_sync_needed(self, data):
        
        if data:
            self.write_gamestate(data)            
        else:
            data = self.load_gamestate()
        
        self.gamestate_send_sync(data)
    
    def gamestate_send_sync(self, data):
        if not data:
            print("NO DATA in gamestate_send_sync WTF?")
        else:
            self.publish("gamestate.sync", data)
        
    def write_gamestate(self, data):
        
        cmd = f"UPDATE gamestates SET blob = (?) WHERE id = {GAMESTATE};"
        ret = self.execute(cmd, (json.dumps(data).encode('utf-8'),))
        retdeu = ret.fetchall()
        self.conn.commit()
        
        
        cmd = f"UPDATE gamestates SET timestamp = {int(time.time())} WHERE id = {GAMESTATE};"
        ret = self.execute(cmd).fetchall()
        ret = self.conn.commit()
        
    def load_gamestate(self):
        row = self.read_id(GAMESTATE, 'gamestates')
        data = AttrDict(json.loads(row['blob']))
        
        return data
        

    ####################################
    ##            PLAYERS             ##
    ##                                ##
    ####################################
    
    def player_update_id(self, id, data):
        for item in data:
            if isinstance(data[item], str):
                value = f"'{data[item]}'"
            else:
                value = data[item]
            cmd = f"UPDATE players SET {item} = {value} WHERE id = {id}"
            print(cmd)
            self.execute(cmd)
        self.conn.commit()
    
    def player_read_channelid(self, channelid):
        data = {}
        cmd = f"SELECT {', '.join(self.tables['players']['schema'])} FROM 'players' WHERE channel_id = {channelid}"
        
        cursor = self.execute(cmd)
        for item in cursor:
            for i, field in enumerate(item):
                data[self.tables[table]['schema'][i]] = field
        return data              
    
    def player_read_id(self, id):
        return self.read_id(id, 'players')
      

    def print_table(self, table="players"):
        cmd = f"SELECT * FROM {table}"
        ret = self.execute(cmd).fetchall()
        for entry in ret:
            print(entry)

    def player_reset_all(self, confirmation):
        if confirmation == "please nuke":
            cmd = f"DELETE FROM players WHERE id"
            self.execute(cmd)
        
    def player_delete_id(self, id):
        cmd = f"DELETE FROM players WHERE id = {id}"
        self.execute(cmd)
        self.conn.commit()
    
    def create_player(self, data={"username":"dummy"}):
        print("receive data:", type(data))
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
        print(cmd)
        c = self.execute(cmd)
        self.conn.commit()
        return c.lastrowid
   
    ####################################
    ##              MISC             ##
    ##                                ##
    ####################################
    def read_id(self, id, table):
        data = {}
        cmd = f"SELECT {', '.join(self.tables[table]['schema'])} FROM {table} WHERE id = {id}"
        
        cursor = self.execute(cmd)
        for item in cursor:
            for i, field in enumerate(item):
                data[self.tables[table]['schema'][i]] = field
        return data              
        
    
    def ensure_table(self, table):
        cmd = f"PRAGMA table_info({table})"
        current_table = self.execute(cmd).fetchall()
        
        if not current_table:
            self.create_table(table)
        
        current_table_fields = [field[1] for field in current_table]
        
        for field in self.tables[table]['schema']:
            if field not in current_table_fields:
                cmd = f"ALTER TABLE {table} ADD COLUMN {field}"
                print(cmd)
                self.execute(cmd)
        
    def create_table(self, table):
        formated_types = "("
        for type in self.tables[table]['types']:
            formated_types = f"{formated_types}{type} {self.tables[table]['types'][type]}, "
        formated_types = formated_types[:-2]+")"

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

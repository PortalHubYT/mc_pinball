import sys
import asyncio
import os
import txaio
txaio.use_asyncio()
from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner

import sqlite3
from sqlite3 import Error

class Database(ApplicationSession):
    async def onJoin(self, details):
        self.name = "pinball"
        self.conn = self.create_connection()
        self.cursor = self.conn.cursor()
        self.execute = self.cursor.execute
        self.types = {"display_name": "TEXT",
                            "username": "TEXT",
                            "alive": "INTEGER",
                            "current_alive":"INTEGER",
                            "best_alive": "INTEGER",
                            "last_checked": "INTEGER",
                            }
        self.schema = [ name for name in self.types]
        
        # a = self.create_player()
        # a = self.create_player()
        # a = self.create_player()
        # a = self.create_player()
        # a = self.create_player()
        # a = self.create_player()

        await self.register(self.reset_all, "data.delete_everything")
        await self.register(self.create_player, "data.create_player")
        await self.register(self.read_id, "data.read_id")
        await self.register(self.update_id, "data.update_id")
        await self.register(self.delete_id, "data.delete_id")
        
    def update_id(self, id, data):
        for item in data:
            if isinstance(data[item], str):
                value = f"'{data[item]}'"
            else:
                value = data[item]
            self.execute(f"UPDATE players SET {item} = {value} WHERE id = {id}")
        self.conn.commit()
    
    def read_id(self, id):
        data = {}
        schema = ["display_name", "username", "best_alive", "alive", "last_checked", "current_alive"]
        
        cmd = f"SELECT {', '.join(schema)} FROM players WHERE id = {id}"
        cursor = self.execute(cmd)
        for item in cursor:
            for i, field in enumerate(item):
                data[schema[i]] = field
        return data                

    def print_table(self, table="players"):
        cmd = f"SELECT * FROM {table}"
        ret = self.execute(cmd).fetchall()
        for entry in ret:
            print(entry)

    def reset_all(self, confirmation):
        if confirmation == "please nuke":
            cmd = f"DELETE FROM players WHERE id"
            print(cmd)
            self.execute(cmd)
        
    def delete_id(self, id):
        cmd = f"DELETE FROM players WHERE id = {id}"
        self.execute(cmd)
        self.conn.commit()
    
    def create_player(self, data={"username":"dummy"}):
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
        c = self.execute(cmd)
        self.conn.commit()
        return c.lastrowid
        
    def ensure_table(self):
        cmd = f"PRAGMA table_info(players)"
        current_table = self.execute(cmd).fetchall()
        
        if not current_table:
            self.create_table()
        
        current_table_fields = [field[1] for field in current_table]
        
        for field in self.schema:
            if field not in current_table_fields:
                cmd = f"ALTER TABLE players ADD COLUMN {field}"
                print(cmd)
                self.execute(cmd)
        
    def create_table(self):
        formated_types = "("
        for type in self.types:
            formated_types = f"{formated_types}{type} {self.types[type]}, "
        formated_types = formated_types[:-2]+")"

        cmd = f"CREATE TABLE players {formated_types};"
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

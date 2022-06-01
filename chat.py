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
from time import time
from math import floor
from input import sanitize_very_strict


class Chat(ApplicationSession):
    def __init__(self, *args):
        super().__init__(*args)

        self.call = self.custom_call

    async def custom_call(self, *args):
        super().call(*args)

    async def onJoin(self, details):
        self.stream_id = "uJcDAS7DdHw"
        self.stream_url = f"https://www.youtube.com/watch?v={self.stream_id}"

        def chat_query():
            while chat.is_alive():
                for c in chat.get().sync_items():
                    message = json.loads(c.json())

                    print("=====MESSAGE================")
                    name = message["author"]["name"]
                    text = "".join(
                        s for s in message["messageEx"] if isinstance(s, str)
                    )
                    print(f"[{name}]: {text}")

                    self.publish("chat.message", pickle.dumps(message))

        # chat = pytchat.create(
        #     video_id=self.stream_url, interruptable=False, hold_exception=False
        # )
        chat = pytchat.create(
            video_id=self.stream_url, interruptable=True, hold_exception=False
        )
        try:
            chat_query()
        except Exception as e:
            raise e


if __name__ == "__main__":
    while True:
        try:
            runner = ApplicationRunner("ws://127.0.0.1:8080/ws", "realm1")
            runner.run(Chat)
        except Exception as e:
            print(e)
            print("Retrying in 3 seconds...")
            asyncio.sleep(3)

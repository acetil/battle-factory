import asyncio
from typing import List
import websockets
from websockets.client import WebSocketClientProtocol
import requests
import json

class PSMessage:
    def __init__ (self, command: str, args: List[str] = [], logged = False, received = False):
        self.logged = logged
        self.command = command
        self.args = args
        self.received = received

    @classmethod
    async def receive (cls, socket: WebSocketClientProtocol):
        msg = await socket.recv()

        logged = msg[0] != "|"

        parts = [i for i in msg.split("|") if i != ""]

        command = parts[0]
        args = parts[1:]

        return cls(command, args, logged, True)

    def getMsgStr (self) -> str:
        if self.logged:
            return f"!{self.command}" + " " + ",".join(self.args)
        elif self.command == "say":
            return "\n".join(self.args)
        else:
            return f"/{self.command}" + " " + ",".join(self.args)

    def __str__ (self):
        return f"{'!' if self.logged else '/'}{self.command} {self.args}"

    async def send (self, socket: WebSocketClientProtocol) -> None:
        if self.received:
            raise RuntimeError("Message was received, cannot be sent back!")
        
        await socket.send(self.getMsgStr())
        


class PSClient:
    def __init__ (self, socket: WebSocketClientProtocol, loginServer: str = "https://play.pokemonshowdown.com/action.php"):
        self.socket: WebSocketClientProtocol = socket
        self.loginServer: str = loginServer
        self.hasLoggedIn: bool = False
        self.challstr: str = None
        self.assertion: str = None

    async def receiveMessage (self) -> PSMessage:
        msg = await PSMessage.receive(self.socket)
        print(f"Received: {msg}")
        return msg
    
    async def sendMessage (self, msg: PSMessage) -> None:
        print(f"Sent: {msg}")
        await msg.send(self.socket)

    async def waitForMessage (self, commands: List[str]) -> PSMessage:
        while True:
            msg: PSMessage = await self.receiveMessage()
            if msg.command in commands:
                return msg
        
    async def login (self, username, password=None) -> None:
        if self.challstr == None:
            msg: PSMessage = await self.waitForMessage(["challstr"])

            self.challstr = "|".join(msg.args)
        
        if password:
            response: requests.Response = requests.post(self.loginServer, data={
                "act" : "login",
                "name" : username,
                "pass" : password,
                "challstr" : self.challstr
            })
        else:
            response: requests.Response = requests.post(self.loginServer, data={
                "act" : "getassertion",
                "userid" : username,
                "challstr" : self.challstr
            })

        if response.status_code == 200:
            print("Received assertion")
            if password:
                self.assertion = json.loads(response.text[1:])["assertion"]
            else:
                self.assertion = response.text

        await self.sendMessage(PSMessage("trn", [username, "0", self.assertion]))

        print("Successfully logged in!")

        #print(await self.receiveMessage())
        


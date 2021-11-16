import asyncio
import websockets

from client import PSClient

async def main (url):
    async with websockets.connect("ws://" + url + "/showdown/websocket") as socket:
        client = PSClient(socket)
        await client.login("absdasdgajshdahs")


if __name__ == "__main__":
    asyncio.run(main("sim.smogon.com:8000"))
    #asyncio.run(main("localhost:8000"))
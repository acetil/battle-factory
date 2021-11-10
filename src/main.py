import asyncio
import websockets

import auth

async def main (url):
    async with websockets.connect("ws://" + url + "/showdown/websocket") as socket:
        await auth.loginUnregistered(socket, "asgdhahsdkjasda", url)


if __name__ == "__main__":
    #asyncio.run(main("sim.smogon.com:8000"))
    asyncio.run(main("localhost:8000"))
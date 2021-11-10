import requests

async def loginUnregistered (socket, username, serverUrl):
    updateStr = await socket.recv()
    print(updateStr)
    challStr: str = await socket.recv()
    print(challStr)
    x = socket.recv()

    print(challStr.split("|", maxsplit=1)[1])

    req = requests.post(f"https://play.pokemonshowdown.com/action.php", params={
        "act" : "getassertion",
        "userid" : username,
        "challstr" : challStr.split("|", maxsplit=2)[2]
    })

    print(req.content)

    print(await x)


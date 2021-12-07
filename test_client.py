import sys
import time
import requests

def runGetRequest (url, args, printFail = True):
    req = requests.get(url, params=args)

    if req.status_code == 200:
        return req.json()
    elif printFail and req.status_code == 400 or req.status_code == 403:
        print(f"Request response [{req.status_code}]: {req.json()['message']}")
    
    return None

def runPostRequest (url, data):
    #print(data)
    req = requests.post(url, json=data)

    if req.status_code == 200:
        #print(req.text)
        return req.json()
    elif req.status_code == 400 or req.status_code == 403:
        print(req.text)
        print(f"Request response [{req.status_code}]: {req.json()['message']}")
        return None
    return None

def printPlayerInfo (info):
    print(f"Player id: {info['player_id']}")
    print(f"Status: {info['status']}")
    print("Team: {}".format(", ".join(i["species"] for i in info["team"])))
    print("Generated: {}".format(", ".join(i["species"] for i in info["generated"])))


def printTournamentInfo (info):
    print(f"Tournament id: {info['name']}")
    print(f"Started: {info['started']}")
    print("Players: ")
    for i in info['players']:
        printPlayerInfo(i)


def getShowdownStr (pokemon):
    s = ""
    s += f"{pokemon['species']} @ {pokemon['item']}\n"
    s += f"Ability: {pokemon['ability']}\n"
    spread = {
        "HP" : pokemon["spread"]["hp"],
        "Atk" : pokemon["spread"]["atk"],
        "Def" : pokemon["spread"]["def"],
        "SpA" : pokemon["spread"]["spatk"],
        "SpD" : pokemon["spread"]["spdef"],
        "Spe" : pokemon["spread"]["speed"]
    }
    s += "EVs: {}\n".format(" / ".join(f"{spread[i]} {i}" for i in spread if spread[i] != 0))
    s += f"{pokemon['spread']['nature']} Nature\n"
    s += f"Shiny: {'Yes' if pokemon['shiny'] else 'No'}\n"
    for i in pokemon['moves']:
        s += f"- {i}\n"

    return s


def choosePokemon (url, tourId, playerId, choices):
    #print(url)
    tourInfo = runGetRequest(f"{url}/api/tournament/info", {
        "name" : tourId
    })
    if tourInfo:
        teamSize = tourInfo["settings"]["team_size"]
    else:
        print("Error getting tournament settings!")
        return
    
    print(f"You may now choose your pokemon! Here are your choices: ")

    for i, p in enumerate(choices):
        print(f"#{i + 1}: ")
        print(getShowdownStr(p))
        print()
    
    chosen = None
    validChoices = False

    while not validChoices:
        if chosen:
            print("Invalid choices")
        chosen = input(f"Enter {teamSize} choices separated by space: ")

        try:
            chosen1 = [i for i in chosen.split(" ") if 1 <= int(i) <= len(choices)]
            #print(teamSize)
            validChoices = len(chosen1) == teamSize
            #print(validChoices)
        except:
            pass
    
    chosenPokemon = [choices[int(i) - 1]['species'] for i in chosen.split(" ")]

    req = runPostRequest(f"{url}/api/player/choose", {
        "tournament" : tourId,
        "player_id" : playerId,
        "choices" : chosenPokemon
    })

    #print(req)

    if req != None:
        print("Pokemon chosen successfully!")
        req = runGetRequest(f"{url}/api/player/info", {
            "tournament" : tourId,
            "player_id" : playerId
        })
        if req:
            with open("battlefactory.txt", "w") as f:
                f.write("\n".join(getShowdownStr(i) for i in req["team"]))
            print("Your team has been written to battlefactory.txt")
        else:
            print("Player info get failed!")
    else:
        print("Failed to choose pokemon!")

def stealPokemon (url, tourId, playerId):
    tourInfo = runGetRequest(f"{url}/api/tournament/info", {
        "name" : tourId
    })

    if tourInfo:
        stealSize = tourInfo["settings"]["steal_size"]
    else:
        print("Error getting tournament settings")
        return

    playerInfo = runGetRequest(f"{url}/api/player/info", {
        "tournament" : tourId,
        "player_id" : playerId
    })

    if playerInfo:
        otherId = playerInfo["battling"]
    else:
        print("Error getting player info")
        return

    otherInfo = runGetRequest(f"{url}/api/player/info", {
        "tournament" : tourId,
        "player_id" : otherId
    })

    if not otherInfo:
        print("Error getting player info")
        return
    

    print(f"Congratulations! You can now steal {otherId}'s pokemon!")
    print(f"As a reminder, here is your team: ")
    for i, p in enumerate(playerInfo["team"]):
        print(f"#{i + 1}: ")
        print(getShowdownStr(p))
    
    print(f"Here are the pokemon you can steal: ")

    for i, p in enumerate(otherInfo["team"]):
        print(f"#{i + 1}: ")
        print(getShowdownStr(p))
    
    chosen = None
    validChoices = False

    while not validChoices:
        if chosen:
            print("Invalid choices")
        chosen = input(f"Enter up to {stealSize} choices to steal separated by space: ")

        try:
            validChoices = chosen.strip() == "" or len([i for i in chosen.split(" ") if 1 <= int(i) <= len(otherInfo["team"])]) <= stealSize
        except:
            pass

    stolenPokemon = [otherInfo["team"][int(i) - 1]['species'] for i in chosen.split(" ")] if chosen.strip() != "" else [] 

    chosen = ""
    validChoices = stolenPokemon == []

    while not validChoices:
        if chosen != "":
            print("Invalid choices")
        chosen = input(f"Enter {len(stolenPokemon)} choices to swap separated by space: ")

        try:
            validChoices = len([i for i in chosen.split(" ") if 1 <= int(i) <= len(playerInfo["team"])]) <= stealSize
        except:
            pass

    swappedPokemon = [playerInfo["team"][int(i) - 1]['species'] for i in chosen.split(" ")] if chosen.strip() != "" else []

    req = runPostRequest(f"{url}/api/player/steal", {
        "tournament" : tourId,
        "player_id" : playerId,
        "pokemon" : stolenPokemon,
        "swapped" : swappedPokemon
    })

    if req == None:
        print("Error sending steal request!")
        return
    
    req = runGetRequest(f"{url}/api/player/info", {
        "tournament" : tourId,
        "player_id" : playerId
    })

    if req == None:
        print("Error getting player info")
        return
    
    print("Steal success!")
    with open("battlefactory.txt", "w") as f:
        f.write("\n".join(getShowdownStr(i) for i in req["team"]))
        print("Your team has been written to battlefactory.txt")

def swapPokemon (url, tourId, playerId):
    playerInfo = runGetRequest(f"{url}/api/player/info", {
        "tournament" : tourId,
        "player_id" : playerId
    })

    if not playerInfo:
        print("Error getting player info")
        return

    if len(playerInfo["generated"]) == 0:
        print("None of your pokemon were stolen!")
        req = runPostRequest(f"{url}/api/player/swap", {
            "tournament" : tourId,
            "player_id" : playerId,
            "kept" : []
        })
        return

    print("Your pokemon have been stolen!")

    print("Here is your remaining team: ")
    for i, p in enumerate(playerInfo["team"]):
        print(f"{i + 1}: ")
        print(getShowdownStr(p))

    print("Please choose from these pokemon to either keep or reroll new ones: ")
    for i, p in enumerate(playerInfo["generated"]):
        print(f"#{i + 1}: ")
        print(getShowdownStr(p))

    chosen = None
    validChoices = False

    while not validChoices:
        if chosen:
            print("Invalid choices")
        chosen = input(f"Enter up to {len(playerInfo['generated'])} choices to keep separated by space: ")

        try:
            validChoices = chosen.strip() == "" or len([i for i in chosen.split(" ") if 1 <= int(i) <= len(playerInfo["generated"])]) <= len(playerInfo['generated'])
        except:
            pass

    swappedPokemon = [playerInfo["generated"][int(i) - 1]['species'] for i in chosen.split(" ")] if chosen.strip() != "" else []

    req = runPostRequest(f"{url}/api/player/swap", {
        "tournament" : tourId,
        "player_id" : playerId,
        "kept" : swappedPokemon
    })

    if req == None:
        print("Error sending swap request!")
        return

    req = runGetRequest(f"{url}/api/player/info", {
        "tournament" : tourId,
        "player_id" : playerId
    })

    if not req:
        print("Error getting player info")
        return
    
    print("Swap success!")
    with open("battlefactory.txt", "w") as f:
        f.write("\n".join(getShowdownStr(i) for i in req["team"]))
        print("Your team has been written to battlefactory.txt")



def nextPlayerAction (req, url, tourId, playerId, hasPrinted):
    if req["status"] == "waiting_battle" or req["status"] == "waiting_stolen" or req["status"] == "waiting_start":
        if not hasPrinted:
            print("Waiting...")
        time.sleep(1)
        return True
    elif req["status"] == "choosing_pokemon":
        #print(url + "*")
        choosePokemon(url, tourId, playerId, req["generated"])
        return False
    elif req["status"] == "battling":
        print(f"You are now battling {req['battling']}!")
        won = input("Did you win (y/n)? ").strip() == "y"
        #print(won)
        runPostRequest(f"{url}/api/battle/result", {
            "tournament" : tourId,
            "player_id" : playerId,
            "result" : won
        })

        return False

    elif req["status"] == "stealing":
        stealPokemon(url, tourId, playerId)
        return False
    elif req["status"] == "swapping":
        swapPokemon(url, tourId, playerId)
        return False
    else:
        print(f"Unknown status: {req['status']}. Please report this to the dev!")
        return hasPrinted


def runPlayerClient (url):
    print("Starting player client!")

    tourId = input("Enter tournament id: ")
    playerId = input("Enter player id: ")

    req = runGetRequest(f"{url}/api/player/info", {
        "tournament" : tourId,
        "player_id" : playerId
    }, False)

    if not req:
        req = runPostRequest(f"{url}/api/player/register", {
            "tournament" : tourId,
            "player_id" : playerId
        })
        if not req:
            print("Player registration failed!")
            return
    hasPrinted = False
    while req:
        hasPrinted = nextPlayerAction(req, url, tourId, playerId, hasPrinted)

        req = runGetRequest(f"{url}/api/player/info", {
            "tournament" : tourId,
            "player_id" : playerId
        })


def runManageClient (url):
    print("Starting management client!")
    tourId = input("Enter tournament id: ")

    req = runGetRequest(f"{url}/api/tournament/info", {
        "name" : tourId
    }, False)

    if not req:
        req = runPostRequest(f"{url}/api/tournament/create", {
            "name" : tourId
        })

        if not req:
            print("Tournament creation failed!")
            return
    print("Available commands: start (starts tournament), tourinfo (gets tournament info), playerinfo <playerid> (gets player info), startbattle <playerid> <playerid> (starts a battle)")
    command = input(">")
    while command.strip() != "exit":
        commands = [i.strip() for i in command.split(" ")]
        if commands[0] == "start":
            req = runPostRequest(f"{url}/api/tournament/start", {
                "name" : tourId
            })
            if req:
                print("Tournament started!")
        elif commands[0] == "playerinfo" and len(commands) == 2:
            req = runGetRequest(f"{url}/api/tournament/info", {
                "name" : tourId
            })

            if req:
                players = req["players"]

                if commands[1] in [i["player_id"] for i in players]:
                    printPlayerInfo([i for i in players if i["player_id"] == commands[1]][0])
        elif commands[0] == "tourinfo":
            req = runGetRequest(f"{url}/api/tournament/info", {
                "name" : tourId
            })

            if req:
                printTournamentInfo(req)
        elif commands[0] == "startbattle" and len(commands) == 3:
            req = runPostRequest(f"{url}/api/battle/start", {
                "tournament" : tourId,
                "player1_id" : commands[1],
                "player2_id" : commands[2]
            })
        elif commands[0] == "clear":
            ans = input("This command clears all the data, including in use. Do you wish to continue (y/n)?")

            if ans.strip() == "y":
                req = runPostRequest(f"{url}/api/test/tournament/clear", {})
                return
        else:
            print("Unknown command!")
        
        command = input(">")



if __name__ == "__main__":
    if sys.argv[1] == "manage":
        runManageClient("http://127.0.0.1:8080")
    elif sys.argv[1] == "player":
        runPlayerClient("http://127.0.0.1:8080")
    else:
        print("Must be either manage or player!")
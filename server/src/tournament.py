from typing import Dict, List
import json

from pokemon import Pokemon
from error import InputError

defaultSettings = {
    "team_size" : 6,
    "draw_size" : 9,
    "steal_size" : 2
}

class Player:
    def __init__ (self, playerId: str, team=[], generated=[]):
        self.playerId = playerId
        self.team: Pokemon = []
        self.generated: Pokemon = []

    @classmethod
    def fromJson (cls, data: Dict):
        return cls(data["player_id"], [Pokemon.fromJson(i) for i in data["team"]], [Pokemon.fromJson(i) for i in data["generated"]])
    
    def toJson (self) -> Dict:
        return {
            "player_id" : self.playerId,
            "team" : [i.getJson() for i in self.team],
            "generated" : [i.getJson() for i in self.generated]
        }


class Tournament:
    def __init__ (self, name: str, settings: Dict = defaultSettings):
        self.name = name
        self.players: List[Player] = []
        self.teamSize: int = settings["team_size"]
        self.drawSize: int = settings["draw_size"]
        self.stealSize: int = settings["steal_size"]
    
    def toJson (self) -> Dict:
        return {
            "name" : self.name,
            "players" : [i.getJson() for i in self.players],
            "settings" : {
                "team_size" : self.teamSize,
                "draw_size" : self.drawSize,
                "steal_size" : self.stealSize
            }
        }

    @classmethod
    def fromJson (cls, data: Dict):
        tour = Tournament(data["name"], data["settings"])
        tour.players = [Player.fromJson(i) for i in data["players"]]
        return tour
    
global tournaments
tournaments: List[Tournament] = None

def loadTournaments ():
    global tournaments
    if tournaments == None:
        try:
            with open("data/tournaments.json") as f:
                tournaments = [Tournament.fromJson(i) for i in json.load(f)["tournaments"]]
        except:
            tournaments = []

def writeTournaments ():
    global tournaments
    try:
        with open("data/tournaments.json", "w") as f:
            json.dump({
                "tournaments" : [i.toJson() for i in tournaments]
            }, f)
    except Exception as e:
        print(e)
    

def createTournament (name: str, settings: Dict):
    print(f"{name} {settings}")
    loadTournaments()
    if name in [i.name for i in tournaments]:
        raise InputError(description=f"Name \"{name}\" is already taken!")
    
    tourSettings = defaultSettings.copy()
    if settings:
        for i in settings:
            if i in tourSettings:
                tourSettings[i] = settings[i]

    tournaments.append(Tournament(name, tourSettings))

    writeTournaments()

    return tournaments[-1].toJson()

def clearTournaments ():
    loadTournaments()
    tournaments.clear()
    writeTournaments()

def getTournamentInfo (name: str):
    loadTournaments()

    if name not in [i.name for i in tournaments]:
        raise InputError(description=f"Tournament \"{name}\" does not exist!")
    
    return [i for i in tournaments if i.name == name][0].toJson()
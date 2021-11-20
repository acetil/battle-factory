from typing import Dict, List
import json

from pokemon import Pokemon
from error import InputError
from usage_scraping import generatePokemon

defaultSettings = {
    "team_size" : 6,
    "draw_size" : 9,
    "steal_size" : 2,
    "ou_scale" : 0.4,
    "uu_scale" : 1.0,
    "ru_scale" : 0.90,
    "nu_scale" : 0.6
}

class Player:
    def __init__ (self, playerId: str, team=[], generated=[], status="waiting_start"):
        self.playerId = playerId
        self.team: List[Pokemon] = team
        self.generated: List[Pokemon] = generated
        self.status = status

    @classmethod
    def fromJson (cls, data: Dict):
        return cls(data["player_id"], [Pokemon.fromJson(i) for i in data["team"]], [Pokemon.fromJson(i) for i in data["generated"]], data["status"])
    
    def toJson (self) -> Dict:
        return {
            "player_id" : self.playerId,
            "team" : [i.getJson() for i in self.team],
            "generated" : [i.getJson() for i in self.generated],
            "status" : self.status
        }
    
    def choosePokemon (self, choices: List[str], teamSize: int) -> None:
        if self.status != "choosing_pokemon":
            raise InputError(description="Can't choose pokemon right now!")

        if len(choices) != teamSize or not all(i in [j.species for j in self.generated] for i in choices):
            print(teamSize)
            print([i for i in choices if i not in [j.species for j in self.generated]])
            raise InputError(description="Team choice incorrect!")
        
        self.team = [i for i in self.generated if i.species in choices]
        self.generated = []

        self.status = "waiting_battle"
class Tournament:
    def __init__ (self, name: str, settings: Dict = defaultSettings):
        self.name = name
        self.players: List[Player] = []
        self.usedPokemon: List[str] = []
        self.teamSize: int = settings["team_size"]
        self.drawSize: int = settings["draw_size"]
        self.stealSize: int = settings["steal_size"]
        self.scalings: Dict[str, float] = {
            "gen8ou" : settings["ou_scale"],
            "gen8uu" : settings["uu_scale"],
            "gen8ru" : settings["ru_scale"],
            "gen8nu" : settings["nu_scale"]
        }
        self.started = False
    
    def toJson (self) -> Dict:
        return {
            "name" : self.name,
            "players" : [i.toJson() for i in self.players],
            "started" : self.started,
            "used_pokemon" : self.usedPokemon,
            "settings" : {
                "team_size" : self.teamSize,
                "draw_size" : self.drawSize,
                "steal_size" : self.stealSize,
                "ou_scale" : self.scalings["gen8ou"],
                "uu_scale" : self.scalings["gen8uu"],
                "ru_scale" : self.scalings["gen8ru"],
                "nu_scale" : self.scalings["gen8nu"]
            }
        }

    @classmethod
    def fromJson (cls, data: Dict):
        tour = Tournament(data["name"], data["settings"])
        tour.players = [Player.fromJson(i) for i in data["players"]]
        tour.started = data["started"]
        tour.usedPokemon = data["used_pokemon"]
        return tour

    def addPlayer (self, player: Player) -> None:
        self.players.append(player)

        if self.started:
            self.genPlayerPokemon(player)


    def getPlayer (self, playerId: str) -> Player:
        players = [i for i in self.players if i.playerId == playerId]

        if len(players) == 0:
            raise InputError(description=f"Player \"{playerId}\" does not exist in tournament \"{self.name}\"")

        return players[0]

    def genPlayerPokemon (self, player: Player):
        genned = generatePokemon(self.drawSize, self.usedPokemon, self.scalings)

        player.generated = genned

        player.status = "choosing_pokemon"

        self.usedPokemon += [i.species for i in genned]
    
    def start (self):
        if self.started:
            raise InputError(description="Tournament already started!")
        
        self.started = True

        for i in self.players:
            self.genPlayerPokemon(i)

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

def getTournamentInfo (name: str) -> Dict:
    loadTournaments()

    if name not in [i.name for i in tournaments]:
        raise InputError(description=f"Tournament \"{name}\" does not exist!")
    
    return [i for i in tournaments if i.name == name][0].toJson()

def registerPlayer (tournament: str, playerId: str) -> Dict:
    loadTournaments()

    if tournament not in [i.name for i in tournaments]:
        raise InputError(description=f"Tournament \"{tournament}\" does not exist!")

    tour = [i for i in tournaments if i.name == tournament][0]

    if playerId in [i.playerId for i in tour.players]:
        raise InputError(description=f"Player \"{playerId}\" already exists in tournament {tournament}!")
    
    player = Player(playerId)
    tour.addPlayer(player)
    writeTournaments()

    return player.toJson()

def getPlayerInfo (tournament: str, playerId: str) -> Dict:
    loadTournaments()

    if tournament not in [i.name for i in tournaments]:
        raise InputError(description=f"Tournament \"{tournament}\" does not exist!")

    tour = [i for i in tournaments if i.name == tournament][0]

    return tour.getPlayer(playerId).toJson()

def startTournament (name: str) -> Dict:
    loadTournaments()

    if name not in [i.name for i in tournaments]:
        raise InputError(description=f"Tournament \"{name}\" does not exist!")

    tour = [i for i in tournaments if i.name == name][0]

    tour.start()

    writeTournaments()

    return tour.toJson()

def choosePokemon (tournament: str, playerId: str, choices: List[str]) -> None:
    loadTournaments()

    if tournament not in [i.name for i in tournaments]:
        raise InputError(description=f"Tournament \"{tournament}\" does not exist!")

    tour = [i for i in tournaments if i.name == tournament][0]

    tour.getPlayer(playerId).choosePokemon(choices, tour.teamSize)

    writeTournaments()
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
    def __init__ (self, playerId: str, team=[], generated=[], status="waiting_start", battling=None):
        self.playerId = playerId
        self.team: List[Pokemon] = team
        self.generated: List[Pokemon] = generated
        self.status = status
        self.battling = battling

    @classmethod
    def fromJson (cls, data: Dict):
        return cls(data["player_id"], [Pokemon.fromJson(i) for i in data["team"]], [Pokemon.fromJson(i) for i in data["generated"]], data["status"],
                data.get("battling", None))
    
    def toJson (self) -> Dict:
        d = {
            "player_id" : self.playerId,
            "team" : [i.getJson() for i in self.team],
            "generated" : [i.getJson() for i in self.generated],
            "status" : self.status
        }

        if self.battling:
            d["battling"] = self.battling

        return d
    
    def choosePokemon (self, choices: List[str], teamSize: int) -> None:
        if self.status != "choosing_pokemon":
            raise InputError(description="Can't choose pokemon right now!")

        if len(choices) != teamSize or not all(i in [j.species for j in self.generated] for i in choices):
            raise InputError(description="Team choice incorrect!")
        
        self.team = [i for i in self.generated if i.species in choices]
        self.generated = []

        self.status = "waiting_battle"

    def completeBattle (self, won: bool) -> None:
        if self.status != "battling":
            raise InputError(description="Not currently battling!")
        
        if won:
            self.status = "stealing"
        else:
            self.status = "waiting_stolen"

    def stealPokemon (self, otherPlayer, pokemon: List[str], swapped: List[str], maxStolen: int) -> None:
        if self.status != "stealing" or otherPlayer.playerId != self.battling:
            raise InputError(description="Cannot steal pokemon!")
        
        if len(pokemon) > maxStolen or len(pokemon) != len(swapped):
            raise InputError(description="Amounts stolen are incorrect!")
        
        if not all(i in [j.species for j in otherPlayer.team] for i in pokemon) or not all(i in [j.species for j in self.team] for i in swapped):
            raise InputError(description="Pokemon stolen or being swapped are incorrect!")

        swappedPokemon = [i for i in self.team if i.species in swapped]
        stolenPokemon = [i for i in otherPlayer.team if i.species in pokemon]

        for i in swappedPokemon:
            self.team.remove(i)
        
        for i in stolenPokemon:
            otherPlayer.team.remove(i)
        
        self.team += stolenPokemon
        otherPlayer.generated += swappedPokemon

        self.status = "waiting_battle"
        self.battling = None
        otherPlayer.status = "swapping"
        otherPlayer.battling = None

    def swapPokemon (self, kept: List[str], tour) -> None:
        if self.status != "swapping":
            raise InputError(description="Cannot swap pokemon!")
        
        if not all(i in [j.species for j in self.generated] for i in kept):
            raise InputError(description="Kept pokemon are incorrect!")
        
        for i in kept:
            self.team.append(self.generated.pop([j for j, v in enumerate(self.generated) if v.species == i][0]))
        
        self.team += tour.genPokemon(len(self.generated))

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
    
    def genPokemon (self, num: int):
        genned = generatePokemon(num, self.usedPokemon, self.scalings)

        self.usedPokemon += [i.species for i in genned]

        return genned
    
    def start (self):
        if self.started:
            raise InputError(description="Tournament already started!")
        
        self.started = True

        for i in self.players:
            self.genPlayerPokemon(i)

    def startBattle (self, player1Id: str, player2Id: str) -> None:
        player1 = self.getPlayer(player1Id)
        player2 = self.getPlayer(player2Id)

        if player1.status != "waiting_battle" or player2.status != "waiting_battle":
            raise InputError(description="Cannot start battle!")
        
        player1.battling = player2Id
        player2.battling = player1Id

        player1.status = "battling"
        player2.status = "battling"

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


def startBattle (tournament: str, player1: str, player2: str) -> None:
    loadTournaments()

    if tournament not in [i.name for i in tournaments]:
        raise InputError(description=f"Tournament \"{tournament}\" does not exist!")

    tour = [i for i in tournaments if i.name == tournament][0]

    tour.startBattle(player1, player2)

    writeTournaments()

def battleResult (tournament: str, playerId: str, won: bool) -> None:
    loadTournaments()

    if tournament not in [i.name for i in tournaments]:
        raise InputError(description=f"Tournament \"{tournament}\" does not exist!")

    tour = [i for i in tournaments if i.name == tournament][0]

    player = tour.getPlayer(playerId)

    player.completeBattle(won)

    writeTournaments()

def stealPokemon (tournament: str, playerId: str, pokemon: List[str], swapped: List[str]) -> None:
    loadTournaments()

    if tournament not in [i.name for i in tournaments]:
        raise InputError(description=f"Tournament \"{tournament}\" does not exist!")

    tour = [i for i in tournaments if i.name == tournament][0]

    player = tour.getPlayer(playerId)
    player.stealPokemon(tour.getPlayer(player.battling), pokemon, swapped, tour.stealSize)

    writeTournaments()

def swapPokemon (tournament: str, playerId: str, kept: List[str]) -> None:
    loadTournaments()

    if tournament not in [i.name for i in tournaments]:
        raise InputError(description=f"Tournament \"{tournament}\" does not exist!")

    tour = [i for i in tournaments if i.name == tournament][0]

    tour.getPlayer(playerId).swapPokemon(kept, tour)

    writeTournaments()
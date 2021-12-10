from typing import Dict, List

from src.pokemon import Pokemon
from src.error import InputError
from src.usage_scraping import generatePokemon

defaultSettings = {
    "team_size" : 6,
    "draw_size" : 9,
    "steal_size" : 2,
    "ou_scale" : 0.6,
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
        tour = cls(data["name"], data["settings"])
        tour.players = [Player.fromJson(i) for i in data["players"]]
        tour.started = data["started"]
        tour.usedPokemon = data["used_pokemon"]
        return tour

    def addPlayer (self, player: Player) -> None:
        if player.playerId in self:
            raise InputError(description=f"Player \"{player.playerId}\" already exists in tournament \"{self.name}\"!")
        
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

    def __contains__ (self, key: str) -> bool:
        return len([i for i in self.players if i.playerId == key]) != 0

    def __str__ (self) -> str:
        return str(self.toJson())
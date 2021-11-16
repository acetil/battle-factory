import random

from typing import Dict, List, Tuple, TypeVar

import config

class PokemonSpread:
    def __init__ (self, nature: str, stats: List[int]):
        self.nature = nature
        self.hp = stats[0]
        self.attack = stats[1]
        self.defence = stats[2]
        self.spattack = stats[3]
        self.spdefence = stats[4]
        self.speed = stats[5]

    @classmethod
    def fromStr (cls, spreadStr: str):
        return cls(spreadStr.split(":")[0], [int(i) for i in spreadStr.split(":")[1].split("/")])
    
    def getJson (self) -> Dict:
        return {
            "nature" : self.nature,
            "hp" : self.hp,
            "atk" : self.attack,
            "def" : self.defence,
            "spatk" : self.spattack,
            "spdef" : self.spdefence,
            "speed" : self.speed
        }


class Pokemon:
    def __init__ (self, species: str, moves: List[str], ability: str, item: str, spread: PokemonSpread, gender: str = None, shiny: bool = False):
        self.species = species
        self.moves = moves
        self.ability = ability
        self.item = item
        self.spread = spread
        self.gender = gender
        self.shiny = shiny
    
    def getJson (self) -> Dict:
        d = {
            "species" : self.species,
            "moves" : self.moves,
            "ability" : self.ability,
            "item" : self.item,
            "spread" : self.spread.getJson(),
            "shiny" : self.shiny
        }
        if self.gender != None:
            d["gender"] = self.gender

        return d

T = TypeVar("T")
def getRandomChoice (choices: List[Tuple[float, T]]) -> T:
    probabilities: List[Tuple[float, T]] = sorted(choices, lambda x: x[0], reverse=True)
    probabilities = [(sum(j[0] for j in probabilities[0:i]), t[1]) for i,t in enumerate(probabilities)]

    rand = random.random()
    l = [i[1] for i in probabilities if rand >= 1 - i[0]]
    while len(l) == 0:
        rand = random.random()
        l = [i[1] for i in probabilities if rand >= 1 - i[0]]
    return l[0]

class PokemonSpecies:
    def __init__ (self, speciesName: str, moves: List[Tuple[float, str]], abilities: List[Tuple[float, str]], items: List[Tuple[float, str]], \
            spreads: List[Tuple[float, PokemonSpread]], usage: float):
        
        self.speciesName = speciesName
        self.moves = moves
        self.abilities = abilities
        self.items = items
        self.usage = usage
        self.spreads = spreads
    
    def generatePokemon (self) -> Pokemon:
        ability = getRandomChoice(self.abilities)
        item = getRandomChoice(self.items)

        spread = getRandomChoice(self.spreads)

        moves: List[str] = []
        while len(moves) < 4:
            moves.append(getRandomChoice([i for i in self.moves if i[1] not in moves]))
        
        return Pokemon(self.speciesName, moves, ability, item, spread, shiny=random.random() <= config.shiny_rate)

    def getUsage (self) -> float:
        return self.usage
    
    def getJson (self) -> Dict:
        return {
            "name" : self.speciesName,
            "moves" : [{"name" : i[1], "usage" : i[0]} for i in self.moves],
            "abilities" : [{"name" : i[1], "usage" : i[0]} for i in self.abilities],
            "items" : [{"name" : i[1], "usage" : i[0]} for i in self.items],
            "usage" : self.usage,
            "spreads" : [{"spread" : i[1].getJson(), "usage": i[0]} for i in self.spreads]
        }

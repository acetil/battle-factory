import random

from typing import Dict, List, Tuple

import config


class Pokemon:
    def __init__ (self, species: str, moves: List[str], ability: str, item: str, gender: str = None, shiny: bool = False):
        self.species = species
        self.moves = moves
        self.ability = ability
        self.item = item
        self.gender = gender
        self.shiny = shiny
    
    def getJson (self) -> Dict:
        d = {
            "species" : self.species,
            "moves" : self.moves,
            "ability" : self.ability,
            "item" : self.item,
            "shiny" : self.shiny
        }
        if self.gender != None:
            d["gender"] = self.gender

        return d

def getRandomChoice (choices: List[Tuple[float, str]]) -> str:
    probabilities = sorted(choices, lambda x: x[0], reverse=True)
    probabilities = [(sum(j[0] for j in probabilities[0:i]), t[1]) for i,t in enumerate(probabilities)]

    rand = random.random()
    return [i[1] for i in probabilities if rand >= 1 - i[0]][0]
    
class PokemonSpecies:
    def __init__ (self, speciesName: str, moves: List[Tuple[float, str]], abilities: List[Tuple[float, str]], items: List[Tuple[float, str]]):
        self.speciesName = speciesName
        self.moves = moves
        self.abilities = abilities
        self.items = items
    
    def generatePokemon (self) -> Pokemon:
        ability = getRandomChoice(self.abilities)
        item = getRandomChoice(self.items)

        moves: List[str] = []
        while len(moves) < 4:
            moves.append(getRandomChoice([i for i in self.moves if i[1] not in moves]))
        
        return Pokemon(self.speciesName, moves, ability, item, shiny=random.random() <= config.shiny_rate)

import json
from typing import Dict, List
from error import InputError
from tournament_data import tournament_data

from tournament import Tournament, Player, defaultSettings

def createTournament (name: str, settings: Dict):
    if name in tournament_data:
        raise InputError(description=f"Name \"{name}\" is already taken!")
    
    tourSettings = defaultSettings.copy()
    if settings:
        for i in settings:
            if i in tourSettings:
                tourSettings[i] = settings[i]

    tour = Tournament(name, tourSettings)

    tournament_data.addTour(tour)

    return tour.toJson()

def clearTournaments ():
    tournament_data.clear()

def getTournamentInfo (name: str) -> Dict:
    return tournament_data[name].toJson()

def registerPlayer (tournament: str, playerId: str) -> Dict:
    with tournament_data.getTour(tournament, True) as tour:
        player = Player(playerId)
        tour.addPlayer(player)
        return player.toJson()


def getPlayerInfo (tournament: str, playerId: str) -> Dict:
    return tournament_data[tournament].getPlayer(playerId).toJson()

def startTournament (name: str) -> Dict:
    with tournament_data.getTour(name, True) as tour:
        tour.start()
        return tour.toJson()


def choosePokemon (tournament: str, playerId: str, choices: List[str]) -> None:
    with tournament_data.getTour(tournament, True) as tour:
        tour.getPlayer(playerId).choosePokemon(choices, tour.teamSize)


def startBattle (tournament: str, player1: str, player2: str) -> None:
    with tournament_data.getTour(tournament, True) as tour:
        tour.startBattle(player1, player2)

def battleResult (tournament: str, playerId: str, won: bool) -> None:
    with tournament_data.getTour(tournament, True) as tour:
        tour.getPlayer(playerId).completeBattle(won)

def stealPokemon (tournament: str, playerId: str, pokemon: List[str], swapped: List[str]) -> None:
    with tournament_data.getTour(tournament, True) as tour:
        player = tour.getPlayer(playerId)
        player.stealPokemon(tour.getPlayer(player.battling), pokemon, swapped, tour.stealSize)

def swapPokemon (tournament: str, playerId: str, kept: List[str]) -> None:
    with tournament_data.getTour(tournament, True) as tour:
        tour.getPlayer(playerId).swapPokemon(kept, tour)
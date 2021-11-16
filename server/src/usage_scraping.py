from random import randint, random
from typing import Dict, List, Union
from datetime import date, timedelta
import requests
import json

from error import InputError
from pokemon import PokemonSpecies, PokemonSpread


def scrapeUsages (usageStr: str) -> Dict[str, float]:
    # Takes the response, splits into lines starts from 5th line and goes to 2nd last line
    # Splits each line into columns: rank, pokemon, usage %, raw, %, real, %
    lines = [[i.strip() for i in l.split("|")][1:-1] for l in usageStr.split("\n")[5:-1]]

    usageDict: Dict[str, float] = {}

    for l in lines[:-1]:
        #print(l)
        usageDict[l[1]] = float(l[2][:-1])
    
    return usageDict

def scrapeSpecies (usageStr: str, setStr: str)-> Dict[str, PokemonSpecies]:
    usages = scrapeUsages(usageStr)
    newSpecies: Dict[str, PokemonSpecies] = {}

    for i in setStr.strip().split(" +----------------------------------------+ \n +----------------------------------------+ "):
        # Areas: pokemon, stats, abilities, items, spreads, moves
        areas = [j.strip() for j in i.strip().split(" +----------------------------------------+ ")]
        areaDict: Dict[str, Union[str, List[str]]] = {"pokemon" : areas[0].strip(" |+-\n")}
        for j in areas[1:]:
            lines = [i.strip(" |\n").strip() for i in j.split("\n")]
            #print(lines)
            areaDict[lines[0]] = lines[1:]
        #print(areaDict)
        
        moves = [(float(i.strip().split(" ")[-1][:-1]) / 100, " ".join(i.strip().split(" ")[:-1]).strip()) for i in areaDict["Moves"] if i.strip().split(" ")[0] != "Other"]
        abilities = [(float(i.strip().split(" ")[-1][:-1]) / 100, " ".join(i.strip().split(" ")[:-1]).strip()) for i in areaDict["Abilities"] if i.strip().split(" ")[0] != "Other"]
        items = [(float(i.strip().split(" ")[-1][:-1]) / 100, " ".join(i.strip().split(" ")[:-1]).strip()) for i in areaDict["Items"] if i.strip().split(" ")[0] != "Other"]
        spreads = [(float(i.strip().split(" ")[-1][:-1]) / 100, PokemonSpread.fromStr(i.strip().split(" ")[0])) for i in areaDict["Spreads"] if i.strip().split(" ")[0] != "Other"]

        newSpecies[areaDict["pokemon"]] = PokemonSpecies(areaDict["pokemon"], moves, abilities, items, spreads, usages[areaDict["pokemon"]] / 100)

    return newSpecies

def tryOpenCache (tier: str, scrapeDate: date) -> Dict[str, PokemonSpecies]:
    try:
        with open(f"data/cache-{scrapeDate.year}.{scrapeDate.month}-{tier}.json") as f:
            jsonDict = json.load(f)

            speciesDict: Dict[str, PokemonSpecies] = {}
            for key in jsonDict:
                speciesDict[key] = PokemonSpecies.fromJson(jsonDict[key])
        return speciesDict

    except:
        return None

def cacheSpeciesDict (tier: str, scrapeDate: date, speciesDict: Dict[str, PokemonSpecies]) -> None:
    with open(f"data/cache-{scrapeDate.year}.{scrapeDate.month}-{tier}.json", "w") as f:
        jsonDict = {}
        for key in speciesDict:
            jsonDict[key] = speciesDict[key].getJson()


        json.dump(jsonDict, f)

def scrapeUsageTime (tier: str, scrapeDate: date) -> Dict[str, PokemonSpecies]:
    #global speciesDict
    if scrapeDate.year < 2020:
        raise InputError(f"Could not find tier \"{tier}\"!")

    speciesDict = tryOpenCache(tier, scrapeDate)
    if speciesDict != None:
        return speciesDict
    
    print(f"Scraping data from smogon for {tier} from {scrapeDate.year}/{scrapeDate.month}!")
    usageResponse = requests.get(f"https://www.smogon.com/stats/{scrapeDate.year}-{scrapeDate.month}/{tier}-1500.txt")
    if usageResponse.status_code != 200:
        scrapeUsageTime(tier, (scrapeDate - timedelta(days=1)).replace(day=1))
        return

    setResponse = requests.get(f"https://www.smogon.com/stats/{scrapeDate.year}-{scrapeDate.month}/moveset/{tier}-1500.txt")
    speciesDict = scrapeSpecies(usageResponse.text, setResponse.text)
    
    cacheSpeciesDict(tier, scrapeDate, speciesDict)

    return speciesDict

def scrapeUsage (tier: str) -> Dict[str, PokemonSpecies]:
    return scrapeUsageTime(tier, (date.today().replace(day=1) - timedelta(days=1)).replace(day=1))



def getUsage (tier: str, species: str) -> Dict:
    #if currentTier != tier:
        #scrapeUsage(tier, date.today().replace(day=1))
    speciesDict = scrapeUsage(tier)
    if species not in speciesDict:
        raise InputError(description=f"Species \"{species}\" not in {tier}!")
    
    return speciesDict[species].getJson()

def getRandom (tier: str, species) -> Dict:
    speciesDict = scrapeUsage(tier)

    if species == None:
        return speciesDict[list(speciesDict.keys())[randint(0, len(speciesDict) - 1)]].generatePokemon().getJson()
    elif species not in speciesDict:
        raise InputError(description=f"Species \"{species}\" not in {tier}!")
    else:
        return speciesDict[species].generatePokemon().getJson()
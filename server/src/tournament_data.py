import json
from typing import Dict, List, Tuple, Union
from threading import Lock, RLock
from error import InputError
from tournament import Tournament

class ReadWriteLock:
    def __init__ (self):
        self.readerLock = Lock()
        self.writerLock = Lock()
        self.readerCounter = 0
        self.writerLocked = False
    
    def lockReader (self) -> None:
        self.readerLock.acquire()
        self.readerCounter += 1
        if self.readerCounter == 1:
            self.writerLock.acquire()
        self.readerLock.release()
    
    def unlockReader (self) -> None:
        self.readerLock.acquire()
        self.readerCounter -= 1
        if self.readerCounter == 0:
            self.writerLock.release()
        self.readerLock.release()
    
    def lockWriter (self) -> None:
        self.writerLock.acquire()
        self.writerLocked = True
    
    def unlockWriter (self) -> None:
        self.writerLocked = False
        self.writerLock.release()

    def __bool__ (self):
        return self.writerLocked

class WriterTournament(Tournament):
    @classmethod
    def fromJson(cls, *args, **kwargs):
        return super(WriterTournament, cls).fromJson(*args, **kwargs)

class TournamentContextManager:
    def __init__ (self, tour: Tournament, lock: Union[Lock, None], data):
        self.tour = tour
        self.lock = lock
        self.data = data
    
    def __enter__ (self) -> Tournament:
        if self.lock != None:
            self.lock.acquire()
        
        return self.tour
    
    def __exit__ (self, exc_type, exc_value, traceback):
        if exc_type == None and isinstance(self.tour, WriterTournament):
            #success
            self.data.saveTour(self.tour)
        if self.lock != None:
            self.lock.release()

        return False

class TournamentData:
    def __init__ (self, savefile: str):
        self.savefile = savefile
        tournamentJson: List[Dict] = []
        try:
            with open(savefile) as f:
                tournamentJson = json.load(f)["tournaments"]
        except:
            pass

        self.tournamentsJson: Dict[str, Dict] = {}
        self.tournamentLocks: Dict[str, Lock] = {}

        for i in tournamentJson:
            self.tournamentsJson[i["name"]] = i
            self.tournamentLocks[i["name"]] = Lock()
        
        self.dataLock = RLock()
        self.personalLock = ReadWriteLock()
        
    def __contains__ (self, item: str) -> bool:
        return item in self.tournamentsJson
    
    def __getitem__ (self, key: Union[str, Tuple[str, bool]]) -> Tournament:
        self.personalLock.lockReader()
        if isinstance(key, str):
            self.personalLock.unlockReader()
            return self[key, False]

        if not key[0] in self:
            self.personalLock.unlockReader()
            raise InputError(description=f"Tournament \"{key[0]}\" does not exist!")

        if key[1]:
            self.tournamentLocks[key[0]].acquire()
    
        val = Tournament.fromJson(self.tournamentsJson[key[0]])
        
        self.personalLock.unlockReader()

        return val

    def getTour (self, key: str, isWriter=False) -> TournamentContextManager:
        self.personalLock.lockReader()

        if not key in self:
            self.personalLock.unlockReader()
            raise InputError(description=f"Tournament \"{key}\" does not exist!")

        if isWriter:
            lock = self.tournamentLocks[key]
            tour = WriterTournament.fromJson(self.tournamentsJson[key])
        else:
            lock = None
            tour = Tournament.fromJson(self.tournamentsJson[key])
        
        self.personalLock.unlockReader()

        return TournamentContextManager(tour, lock, self)


    def saveTour (self, tour: Tournament) -> None:
        with self.dataLock:
            if tour.name not in self:
                raise RuntimeError(f"Tournament \"{tour.name}\" does not exist!")
            elif not isinstance(tour, WriterTournament):
                raise RuntimeError(f"Cannot save non-writable tournament!")

            self.tournamentsJson[tour.name] = tour.toJson()
        
            self.saveData()
    

    def addTour (self, tour: Tournament) -> None:
        with self.dataLock:
            if tour.name in self:
                raise InputError(description=f"Tournament \"{tour.name}\" already exists!")
            else:
                self.tournamentLocks[tour.name] = Lock()
                self.tournamentsJson[tour.name] = tour.toJson()
            self.saveData()

    def saveData (self) -> None:
        with self.dataLock:
            with open(self.savefile, "w") as f:
                json.dump({
                        "tournaments" : [self.tournamentsJson[i] for i in self.tournamentsJson]
                    }, f)
        
    
    def __setitem__ (self, key: str, item: Tournament) -> None:
        with self.dataLock:
            if key in self:
                if not self.tournamentLocks[key].locked():
                    raise RuntimeError("Reader incorrectly wrote / tried to write to data!")
            
                self.tournamentLocks[key].release()
            else:
                self.tournamentLocks[key] = Lock()

            self.tournamentsJson[key] = item.toJson()

            self.saveData()
    
    def closeWriter (self, key: str) -> None:
        if self.tournamentLocks[key].locked():
            self.tournamentLocks[key].release()
    
    def clear (self):
        self.personalLock.lockWriter()
        with self.dataLock:
            self.tournamentsJson.clear()
            self.saveData()
        
        self.personalLock.unlockWriter()



        
global tournament_data
tournament_data = TournamentData("data/tournaments.json")
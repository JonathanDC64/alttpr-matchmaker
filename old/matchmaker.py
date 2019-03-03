import alttpr_api
import chat
from datetime import datetime, timedelta
from uuid import UUID, uuid4
from typing import List, Dict

class Settings:

    difficulty = {
        'normal' : "Normal",
        'easy' : "Easy",
        'hard' : "Hard",
        'expert' : "Expert",
        'insane' : "Insane",
        'crowdControl' : "Crowd Control"
    }

    goal = {
       "ganon": "Defeat Ganon",
       "dungeons": "All Dungeons",
       "pedestal": "Master Sword Pedestal",
       "triforce-hunt": "Triforce Pieces"
    }

    logic = {
        'NoGlitches': "No Glitches",
        'OverworldGlitches': "Overworld Glitches",
        'MajorGlitches': "Major Glitches",
        'None': "None (I know what I’m doing)"
    }

    mode = {
        'standard' : "Standard",
        'open' : "Open",
        'inverted' : "Inverted"
    }

    variation = {
        'none': "None",
        'timed-race': "Timed Race",
        'timed-ohko': "Timed OHKO",
        'ohko': "OHKO",
        'key-sanity': "Keysanity",
        'retro': "Retro"
    }

    weapons = {
        'uncle': "Uncle Assured",
        'randomized': "Randomized",
        'swordless': "Swordless"
    }

    def __init__(self, difficulty: str, enemizer: bool, goal : str, lang: str, logic: str, mode: str, spoilers: bool, tournament: bool, variation: str, weapons: str) -> None:
        self.difficulty = difficulty
        self.enemizer = bool(enemizer)
        self.goal = goal
        self.lang = lang
        self.logic = logic
        self.mode = mode
        self.spoilers = bool(spoilers)
        self.tournament = bool(tournament)
        self.variation = variation
        self.weapons = weapons

    def to_dict(self) -> dict:
        return {
            "difficulty": self.difficulty,
            "enemizer": self.enemizer,
            "lang": self.lang,
            "logic": self.logic,
            "mode": self.mode,
            "spoilers": self.spoilers,
            "tournament": self.tournament,
            "variation": self.variation,
            "weapons": self.weapons
        }

class Player:

    def __init__(self, name: str) -> None:
        self.__name: str = name
        self.__id: UUID = uuid4()     
    
    def name(self) -> str:
        return self.__name

    def set_name(self, name: str) -> None:
        self.__name = name

    def get_id(self) -> str:
        return str(self.__id)

class Room:

    #MAX_PLAYERS: int = 4
    player_pool: Dict[str, Player] = {} # Holds all players on the server

    def __init__(self, settings: Settings, creator: Player) -> None:
        self.__players: Dict[str, Player] = {}
        self.__settings: Settings = settings
        self.__seed: dict = alttpr_api.generate_seed(settings.to_dict())
        self.__seed.pop('patch') #patch data is not needed
        self.__chat = chat.get_chat_room(self.__seed['hash'])
        self.__creator = creator
        self.__create_time = datetime.now()
        self.__expire_time = self.__create_time + timedelta(hours = 6) # Room expires in 6 hours
        self.add_player(creator)

    def add_player(self, player: Player) -> None:
        #if not self.is_full():
        self.__players[player.get_id()] = player
        Room.add_global_player(player)

    def remove_player(self, player: Player) -> None:
        if player.get_id() in self.__players.keys():
            self.__players.pop(player.get_id())
            Room.remove_global_player(player)

    @staticmethod
    def add_global_player(player: Player):
        Room.player_pool[player.get_id()] = player

    @staticmethod
    def remove_global_player(player: Player):
        Room.player_pool.pop(player.get_id())

    def get_players(self) -> List[Player]:
        return self.__players

    def num_players(self):
        return len(self.__players)
                
    #def is_full(self) -> bool:
    #    return len(self.__players) == self.MAX_PLAYERS
    
    def get_seed_data(self) -> dict:
        return self.__seed

    def get_url(self) -> str:
        return alttpr_api.get_url(self.__seed['hash'])

    def get_id(self) -> str:
        return f'alttpr_{self.__seed["hash"]}'

    def get_chat_html(self, player: Player) -> str:
        return chat.get_chat_html(self.__chat, player.name())

    def get_settings(self) -> Settings:
        return self.__settings

    def get_creator(self) -> Player:
        return self.__creator

    def get_expire_time(self) -> str:
        expire_time = self.__expire_time - datetime.now()
        total_seconds = max(expire_time.seconds, 0)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = (total_seconds % 3600) % 60
        return f'{hours} hours, {minutes} minutes, {seconds} seconds'


class RoomManager:

    MAX_ROOMS = 100

    def __init__(self) -> None:
        self.__rooms: Dict[str, Room] = {}

    def create_room(self, settings: Settings, creator: Player) -> Room:
        if not self.is_full():
            room: Room = Room(settings, creator)
            self.__rooms[room.get_id()] = room
            return room
        return None

    def remove_room(self, id: str):
        if id in self.__rooms.keys():
            self.__rooms.pop(id)

    def get_rooms(self) -> List[Room]:
        return self.__rooms

    def is_full(self) -> bool:
        return len(self.__rooms) == self.MAX_ROOMS
from dataclasses import dataclass
import ast
import json
from typing import List, Tuple, Dict


class Entry:
    type: str = None

    def get_ddb_dict(self) -> Dict:

        attrs = self.get_annotations()

        t = {}

        for attr, typ in attrs.items():
            val = self.__getattribute__(attr)

            if val is None:
                continue
            
            if typ == int:
                t[attr] = {"N": str(val)}
            elif typ == bool:
                t[attr] = {"BOOL": val}
            elif typ == str:
                t[attr] = {"S": val}
            else:
                t[attr] = {"S": str(val).replace("'", "\"")}

        return t

    @classmethod
    def get_annotations(cls) -> Dict[str, str]:
        """
        Returns a dict where keys are class attributes and values are attribute types
        """
        attrs = dict(cls.__annotations__)
        return attrs


@dataclass
class Game(Entry):
    id: str                         # PK
    words_per_player: int           # Number of words each player submits
    r1_sec: int                     # Seconds per turn in Round 1
    r2_sec: int                     # Seconds per turn in Round 2
    r3_sec: int                     # Seconds per turn in Round 3
    started: bool = False           # Whether this game has started the first round
    complete: bool = False          # Whether this game is finished
    captain_id: str = None
    queue: List[List[str]] = None   # The queue structure for turns
    round: int = None               # What round is active: 1, 2, 3
    time_remaining: int = None      # The number of seconds remaining in the last turn
    type: str = "game"

    def __post_init__(self):
        """
        When init from DDB, queue is a string
        """
        if type(self.queue) == str:
            self.queue = ast.literal_eval(self.queue)


@dataclass
class Player(Entry):
    id: str             # PK
    gid: str            # FK: What game is the player in?
    name: str           # What is the name of the player?
    team: str = None    # What team is the player on?  "a" or "b"
    ready: bool = False # Whether they player has submitted words
    type: str = "player"


@dataclass
class Word(Entry):
    id: str             # PK
    pid: str            # FK: What player submitted the word?
    gid: str            # FK: What game is the word in?
    word: str           # The actual word
    r1_done: bool = False # Whether this word has been guessed in r1
    r2_done: bool = False # Whether this word has been guessed in r2
    r3_done: bool = False # Whether this word has been guessed in r3
    type: str = "word"


@dataclass
class Attempt(Entry):
    id: str         # PK
    wid: str        # FK: What word was attempted?
    pid: str        # FK: What player was giving the clue?
    gid: str        # FK: What game did the attempt occur in?
    round: int      # What round did this attempt occur in?
    success: bool   # Did the team guessing get the point?
    point: bool     # Did the attempt result in a point?
    seconds: int    # How long did the attempt last?
    team: str       # Which team made this attempt
    type: str = "attempt"



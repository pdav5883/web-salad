from dataclasses import dataclass
import ast
import json
from typing import List, Tuple, Dict


class Entry:
    table: str = None

    def __str__(self):
        _, rep_list = self.get_attr_rep_lists()
        return "(" + ",".join(rep_list) + ")"

    def get_attr_rep_lists(self) -> Tuple[List[str], List[str]]:
        """
        Grabs lists of the attributes of the entry and the represenation of their assigned values in SQL string
        """
        attrs = self.get_annotations()

        rep = list()

        for attr, typ in attrs.items():
            val = self.__getattribute__(attr)
            if val is None:
                rep.append(f"NULL")
            elif typ == str:
                rep.append(f"'{val}'")
            elif typ == int:
                rep.append(f"{val}")
            elif typ == bool:
                rep.append(f"{int(val)}")
            else:
                list_str = str(val).replace("'", "\"")
                rep.append(f"'{list_str}'")

        return list(attrs.keys()), rep

    @classmethod
    def get_annotations(cls) -> Dict[str, str]:
        """
        Returns a dict where keys are class attributes and values are attribute types
        """
        attrs = dict(cls.__annotations__)
        del attrs["table"]
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
    queue: List[List[str]] = None   # The queue structure for turns
    round: int = None               # What round is active: 1, 2, 3
    time_remaining: int = None      # The number of seconds remaining in the last turn
    table: str = "game"

    def __post_init__(self):
        """
        When init from SQL row, queue is a string
        """
        if type(self.queue) == str:
            self.queue = ast.literal_eval(self.queue)


@dataclass
class Player(Entry):
    id: str             # PK
    gid: str            # FK: What game is the player in?
    name: str           # What is the name of the player?
    captain: bool       # Whether this player is the captain
    team: str = None    # What team is the player on?  "a" or "b"
    table: str = "player"


@dataclass
class Word(Entry):
    id: str             # PK
    pid: str            # FK: What player submitted the word?
    gid: str            # FK: What game is the word in?
    word: str           # The actual word
    table: str = "word"


@dataclass
class Attempt(Entry):
    id: str         # PK
    wid: str        # FK: What word was attempted?
    pid: str        # FK: What player was giving the clue?
    gid: str        # FK: What game did the attempt occur in?
    round: int      # What round did this attempt occur in?
    point: bool     # Did someone get a point?
    success: bool   # Did the team guessing get the point?
    seconds: int    # How long did the attempt last?
    table: str = "attempt"





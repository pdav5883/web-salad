from dataclasses import dataclass
from typing import List, Tuple, Dict


@dataclass
class Game:
    gid: str                        # PK
    words_per_player: int           # Number of words each player submits
    r1_sec: int                     # Seconds per turn in Round 1
    r2_sec: int                     # Seconds per turn in Round 2
    r3_sec: int                     # Seconds per turn in Round 3
    started: bool = False           # Whether this game has started the first round
    complete: bool = False          # Whether this game is finished
    captain_pid: str = None         # The player ID of the captain
    queue: List[List[str]] = None   # The queue structure for turns
    score_a: int = 0                # The score for team a
    score_b: int = 0                # The score for team b
    round: int = None               # What round is active: 1, 2, 3
    time_remaining: int = None      # The number of seconds remaining in the last turn


@dataclass
class Player:
    pid: str            # PK
    gid: str            # FK: What game is the player in?
    name: str           # What is the name of the player?
    team: str = None    # What team is the player on?  "a" or "b"


@dataclass
class Word:
    wid: str            # PK
    pid: str            # FK: What player submitted the word?
    gid: str            # FK: What game is the word in?
    word: str           # The actual word
    used: bool = False  # Whether the words has been used in the current round


@dataclass
class Attempt:
    aid: str        # PK
    wid: str        # FK: What word was attempted?
    gid: str        # FK: What game did the attempt occur in?
    pid: str        # FK: What player was giving the clue?
    round: int      # What round did this attempt occur in?
    success: bool   # Did the team guessing get the point?
    failure: bool   # Did the team guessing give the point to the other team?
    seconds: int    # How long did the attempt last?





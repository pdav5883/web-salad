import string
import random
import json
from typing import List, Tuple
import copy

gpath = "data/games.txt"
ppath = "data/players.txt"
wpath = "data/words.txt"


def auth_game(req) -> bool:
    """
    Check cookies for game ID
    """
    gid = req.cookies.get("gid", None)
    if gid:
        return is_valid_game_id(gid)
    else:
        return False


def auth_player(req) -> bool:
    """
    Check cookies for valid player ID
    """
    pid = req.cookies.get("pid", None)
    if pid:
        return is_valid_player_id(pid)
    else:
        return False


def add_game(gid, gdata) -> bool:
    games = get_games()

    # don't want to overwrite a game that already exists
    if gid in games:
        return False

    games[gid] = gdata

    with open(gpath, "w") as fptr:
        json.dump(games, fptr)

    return True


def add_player(pid, pdata) -> bool:
    players = get_players()
    players[pid] = pdata

    with open(ppath, "w") as fptr:
        json.dump(players, fptr)

    return True


def add_words(new_words: List[str]) -> True:
    words = get_words()

    for new_word in new_words:
        wid = create_rand_id()
        wdata = {"word": new_word, "used": False}
        words[wid] = wdata

    with open(wpath, "w") as fptr:
        json.dump(words, fptr)

    return True


def get_games() -> dict:
    with open(gpath, "r") as fptr:
        return json.load(fptr)


def get_players() -> dict:
    with open(ppath, "r") as fptr:
        return json.load(fptr)


def get_words() -> dict:
    with open(wpath, "r") as fptr:
        return json.load(fptr)


def get_words_remaining() -> List[List[str]]:
    words = get_words()
    return [[wid, wdata["word"]] for wid, wdata in words.items() if not wdata["used"]]


def get_game(gid):
    return get_games().get(gid, None)


def get_time_remaining(gid):
    return get_games().get(gid).get("time_remaining")


def get_player(pid):
    return get_players().get(pid, None)


def get_player_name(pid):
    return get_player(pid).get("pname")


def update_games(games: dict):
    with open(gpath, "w") as fptr:
        json.dump(games, fptr)


def update_players(players: dict):
    with open(ppath, "w") as fptr:
        json.dump(players, fptr)


def update_words(words: dict):
    with open(wpath, "w") as fptr:
        json.dump(words, fptr)


def reset_words(words: dict) -> dict:
    for wdata in words.values():
        wdata["used"] = False
    return words


def is_valid_game_id(gid) -> bool:
    return gid in get_games()


def is_valid_player_id(pid) -> bool:
    return pid in get_players()


def is_game_started(gid) -> bool:
    return get_games().get(gid, {}).get("started", False)


def is_player_captain(pid) -> bool:
    return get_players().get(pid).get("captain")


def create_rand_id(n=10) -> str:
    chars = string.ascii_uppercase
    return "".join(random.choice(chars) for _ in range(n))


def bump_player_queue(queue: List[List[str]]) -> Tuple[str, str, List[List[str]]]:
    """
    Increment the player queue.
    Return the current player, next player, and new queue
    """
    q = copy.deepcopy(queue)

    current_team = q.pop(0)
    current_player = current_team.pop(0)
    current_team.append(current_player)
    q.append(current_team)
    next_player = q[0][0]

    return current_player, next_player, q

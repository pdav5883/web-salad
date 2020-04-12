import string
import random
import json
from typing import List, Tuple, Union
import copy
import sqlite3

from model import Entry, Game, Player, Word, Attempt

conn = sqlite3.connect("data/salad.db")

gpath = None
ppath = None
wpath = None


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


def entry_exists_by_obj(entry: Entry) -> bool:
    """
    Checks if the ID of the proposed entry already exists in the DB
    """
    query = f"SELECT 1 FROM {entry.table} WHERE id = '{entry.id}'"
    return True if conn.execute(query).fetchone() else False


def entry_exists_by_id(entry_id: str, entry_type: type) -> bool:
    """
    Checks if the ID already exists in the DB
    """
    query = f"SELECT 1 FROM {entry_type.table} WHERE id = '{entry_id}'"
    return True if conn.execute(query).fetchone() else False


def get_entry_by_id(entry_id: str, entry_type: type) -> Entry:
    """
    Return the entry with given id in given table. None if entry does not exist
    """
    query = f"SELECT * FROM {entry_type.table} WHERE id = '{entry_id}'"
    res = conn.execute(query).fetchone()

    if res:
        return entry_type(*res)
    else:
        return None


def add_entry(entry: Entry) -> bool:
    """
    Insert an entry into the correct DB table. Return True if entry successful
    """
    if entry_exists_by_obj(entry):
        print(f"Entry in {entry.table} with id {entry.id} already exists")
        return False

    query = f"INSERT INTO {entry.table} VALUES {entry.__str__()}"
    conn.execute(query)
    conn.commit()
    return True


def add_entries(entries: List[Entry]) -> bool:
    """
    Insert a list of entries into the correct DB table. Commit and return bool if all successful
    """
    for entry in entries:
        if entry_exists_by_obj(entry):
            print(f"Entry in {entry.table} with id {entry.id} already exists...rolling back previous additions")
            conn.rollback()
            return False

        query = f"INSERT INTO {entry.table} VALUES {entry.__str__()}"
        conn.execute(query)

    conn.commit()
    return True


def update_entry(entry: Entry) -> bool:
    """
    Update an entry in the database with new values, return whether update was success
    """
    if not entry_exists_by_obj(entry):
        print(f"Entry in {entry.table} with id {entry.id} does not exist")
        return False

    col_list, val_list = entry.get_attr_rep_lists()
    set_str = ",".join([f"{col} = {val}" for col, val in zip(col_list, val_list)])

    query = f"UPDATE {entry.table} SET {set_str} WHERE id = '{entry.id}'"
    conn.execute(query)
    conn.commit()
    return True


def update_entries(entries: List[Entry]) -> bool:
    """
    Update a list of entries in the correct DB table. Commit and return bool if all successful
    """
    for entry in entries:
        if not entry_exists_by_obj(entry):
            print(f"Entry in {entry.table} with id {entry.id} does not exist...rolling back previous updates")
            conn.rollback()
            return False

        col_list, val_list = entry.get_attr_rep_lists()
        set_str = ",".join([f"{col} = {val}" for col, val in zip(col_list, val_list)])

        query = f"UPDATE {entry.table} SET {set_str} WHERE id = '{entry.id}'"
        conn.execute(query)

    conn.commit()
    return True


def get_words_remaining(gid: str) -> List[Word]:
    """
    Get a list of Words that have not yet been used in the current round
    """
    query = f"SELECT * FROM word WHERE gid = '{gid}' AND used = 0"

    words = list()
    for word_args in conn.execute(query):
        words.append(Word(*word_args))

    return words




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
    return True
    # return gid in get_games()


def is_valid_player_id(pid) -> bool:
    return True
    # return pid in get_players()


def is_game_started(gid) -> bool:
    return True
    # return get_games().get(gid, {}).get("started", False)


def is_player_captain(pid) -> bool:
    return True
    # return get_players().get(pid).get("captain")


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

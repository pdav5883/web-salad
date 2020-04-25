import string
import random
import json
from typing import List, Tuple, Union, Dict
import copy
import sqlite3
import ast

from model import Entry, Game, Player, Word, Attempt

conn = sqlite3.connect("data/salad.db")

#######################################
# Generic Database Interaction
#######################################


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


#######################################
# Back-End Methods
#######################################


def auth_game(req) -> bool:
    """
    Check cookies for game ID
    """
    gid = req.cookies.get("gid", None)
    if gid:
        return entry_exists_by_id(gid, Game)
    else:
        return False


def auth_player(req) -> bool:
    """
    Check cookies for valid player ID
    """
    pid = req.cookies.get("pid", None)
    if pid:
        return entry_exists_by_id(pid, Player)
    else:
        return False


def get_players_by_game_id(gid: str) -> List[Player]:
    """
    Get all the players in this game
    """
    query = f"SELECT * FROM player WHERE gid = '{gid}'"
    return [Player(*res) for res in conn.execute(query).fetchall()]


def get_teams_by_game_id(gid: str) -> Tuple[List[str], List[str]]:
    """
    Return player names by team
    """
    players = get_players_by_game_id(gid)
    teams = {"a": list(), "b": list()}

    for player in players:
        teams[player.team].append(player.name)

    return teams["a"], teams["b"]


def get_words_remaining(gid: str) -> List[Word]:
    """
    Get a list of Words that have not yet been used in the current round
    """
    query = f"SELECT word.* FROM word " \
        f"WHERE word.gid = {gid} " \
        f"AND NOT EXISTS " \
        f"(SELECT 1 FROM attempt INNER JOIN game " \
        f"WHERE word.id = attempt.wid " \
        f"AND game.round = attempt.round " \
        f"AND attempt.point = 1);"

    words = list()
    for word_args in conn.execute(query):
        words.append(Word(*word_args))

    return words


def get_attempts_by_game_id(gid: str) -> List[Attempt]:
    """
    All the attempts that have happened in this game
    """
    query = f"SELECT * FROM attempt WHERE gid = '{gid}'"

    attempts = list()
    for attempt_args in conn.execute(query):
        attempts.append(Attempt(*attempt_args))

    return attempts


def get_point_attempts_by_team_by_game_id(gid: str) -> Tuple[List[Attempt], List[Attempt]]:
    """
    Organize attempts that resulted in a point by team. Team A is first, Team B is second
    """
    query_a = f"SELECT attempt.* FROM attempt " \
        f"WHERE attempt.gid = '{gid}' " \
        f"AND attempt.point = 1 " \
        f"AND player.team = 'a' " \
        f"INNER JOIN player"
    query_b = f"SELECT attempt.* FROM attempt " \
        f"WHERE attempt.gid = '{gid}' " \
        f"AND attempt.point = 1 " \
        f"AND player.team = 'b' " \
        f"INNER JOIN player"

    attempts_a = list()
    for attempt_args in conn.execute(query_a):
        attempts_a.append(Attempt(*attempt_args))

    attempts_b = list()
    for attempt_args in conn.execute(query_b):
        attempts_b.append(Attempt(*attempt_args))

    return attempts_a, attempts_b


def get_scores_by_game_id(gid: str) -> Tuple[int, int]:
    """
    Return total scores for team A and team B
    """
    attempts_a, attempts_b = get_point_attempts_by_team_by_game_id(gid)

    score_a = score_b = 0

    for attempt in attempts_a:
        if attempt.success:
            score_a += 1
        else:
            score_b += 1

    for attempt in attempts_b:
        if attempt.success:
            score_b += 1
        else:
            score_a += 1

    return score_a, score_b


def create_rand_id(n=10) -> str:
    chars = string.ascii_uppercase
    return "".join(random.choice(chars) for _ in range(n))


def bump_player_queue(queue: str) -> Tuple[str, str, str]:
    """
    Increment the player queue.

    Queue is input/output as a string rep of a List[List[str]] of player ids. Must be in string format for SQLite
    storage.

    Return the current player, next player, and new queue
    """
    q = ast.literal_eval(queue)

    current_team = q.pop(0)
    current_player = current_team.pop(0)
    current_team.append(current_player)
    q.append(current_team)
    next_player = q[0][0]

    return current_player, next_player, str(q)

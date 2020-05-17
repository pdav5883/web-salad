import os
import string
import random
import json
from typing import List, Tuple, Union, Dict
import copy
import sqlite3
import ast
from collections import defaultdict

from model import Entry, Game, Player, Word, Attempt

root_dir = os.path.dirname(os.path.abspath(__file__))
conn = sqlite3.connect(os.path.join(root_dir,"data","salad.db"), check_same_thread=False)

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


def get_captain_by_game_id(gid: str) -> Player:
    """
    The captain of the game
    """
    query = f"SELECT player.* FROM player " \
        f"INNER JOIN game ON game.id = player.gid " \
        f"WHERE game.id = '{gid}' AND player.id = game.captain_id"
    res = conn.execute(query).fetchone()

    if res:
        return Player(*res)
    else:
        return None


def get_players_ready_by_game_id(gid: str, pids: List[str]) -> List[bool]:
    """
    Return a list of whether each player has submitted words
    """
    query = f"SELECT DISTINCT pid FROM word WHERE gid = '{gid}'"
    ready_players = [res[0] for res in conn.execute(query).fetchall()]

    ready = []

    for pid in pids:
        ready.append(pid in ready_players)

    return ready


def player_exists_by_name_game_id(gid: str, name: str) -> bool:
    """
    Return whether a player with given name already exists in the game
    """
    query = f"SELECT 1 FROM player WHERE gid = '{gid}' AND name = '{name}'"
    return True if conn.execute(query).fetchone() else False


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
        f"WHERE word.gid = '{gid}' " \
        f"AND NOT EXISTS " \
        f"(SELECT 1 FROM attempt " \
        f"INNER JOIN game ON game.id = attempt.gid " \
        f"WHERE attempt.wid = word.id " \
        f"AND game.round = attempt.round " \
        f"AND attempt.success IS NOT NULL);"

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
        f"INNER JOIN player ON player.id = attempt.pid " \
        f"WHERE attempt.gid = '{gid}' " \
        f"AND attempt.success IS NOT NULL " \
        f"AND player.team = 'a'"
    query_b = f"SELECT attempt.* FROM attempt " \
        f"INNER JOIN player ON player.id = attempt.pid " \
        f"WHERE attempt.gid = '{gid}' " \
        f"AND attempt.success IS NOT NULL " \
        f"AND player.team = 'b'"

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


def get_scores_by_round_by_game_id(gid: str) -> Tuple[List[int], List[int]]:
    """
        Return total scores for team A and team B as a list by round
        """
    attempts_a, attempts_b = get_point_attempts_by_team_by_game_id(gid)

    score_a = 3 * [0]
    score_b = 3 * [0]

    for attempt in attempts_a:
        if attempt.success:
            score_a[attempt.round - 1] += 1
        else:
            score_b[attempt.round - 1] += 1

    for attempt in attempts_b:
        if attempt.success:
            score_b[attempt.round - 1] += 1
        else:
            score_a[attempt.round - 1] += 1

    return score_a, score_b


def get_team_stats(gid: str, team: str) -> List[Tuple[str, int, int, int, int]]:
    """
    Return a list of tuples with stats for a full team. Each entry in list corresponds to player. List is sorted by
    total points scored by player. Each tuple contains name str, r1 score int, r2 score int, r3 score int, total score
    int. There is an extra entry for team total.
    """
    query = f"SELECT player.name, " \
        f"(SELECT COUNT(attempt.id) FROM attempt WHERE player.id = attempt.pid AND attempt.round = 1 AND attempt.success = 1), "\
        f"(SELECT COUNT(attempt.id) FROM attempt WHERE player.id = attempt.pid AND attempt.round = 1 AND attempt.success = 0), "\
        f"(SELECT COUNT(attempt.id) FROM attempt WHERE player.id = attempt.pid AND attempt.round = 2 AND attempt.success = 1), "\
        f"(SELECT COUNT(attempt.id) FROM attempt WHERE player.id = attempt.pid AND attempt.round = 2 AND attempt.success = 0), "\
        f"(SELECT COUNT(attempt.id) FROM attempt WHERE player.id = attempt.pid AND attempt.round = 3 AND attempt.success = 1), "\
        f"(SELECT COUNT(attempt.id) FROM attempt WHERE player.id = attempt.pid AND attempt.round = 3 AND attempt.success = 0) "\
        f"FROM player WHERE player.gid = '{gid}' AND player.team = '{team}'"
    player_data = [(pdata[0],
                    pdata[1] - pdata[2],
                    pdata[3] - pdata[4],
                    pdata[5] - pdata[6],
                    pdata[1] - pdata[2] + pdata[3] - pdata[4] + pdata[5] - pdata[6])
                   for pdata in conn.execute(query).fetchall()]
    player_data.sort(key=lambda x: x[4], reverse=True)

    total_r1 = sum([x[1] for x in player_data])
    total_r2 = sum([x[2] for x in player_data])
    total_r3 = sum([x[3] for x in player_data])
    total = total_r1 + total_r2 + total_r3

    player_data.append(("Total", total_r1, total_r2, total_r3, total))

    return player_data


def get_word_stats(gid: str) -> List[Tuple[str, int, int, int, int]]:
    """
    Each entry in list is tuple of word data. Tuple contains word str, r1 time, r2 time, r3 time, avg time. List is
    sorted by avg time. Extra list entry for total avg.
    """
    """
    query_words = f"SELECT word.word, attempt.round, SUM(attempt.seconds) " \
        f"FROM word " \
        f"INNER JOIN attempt ON word.id = attempt.wid " \
        f"WHERE word.gid = '{gid}' " \
        f"GROUP BY word.word, attempt.round"
    """
    query = f"SELECT word.word, " \
        f"(SELECT SUM(attempt.seconds) FROM attempt WHERE word.id = attempt.wid AND attempt.round = 1), " \
        f"(SELECT SUM(attempt.seconds) FROM attempt WHERE word.id = attempt.wid AND attempt.round = 2), " \
        f"(SELECT SUM(attempt.seconds) FROM attempt WHERE word.id = attempt.wid AND attempt.round = 3) " \
        f"FROM word WHERE word.gid = '{gid}'"

    word_data = [(wdata[0], wdata[1], wdata[2], wdata[3], round(sum(wdata[1:]) / 3, 1))
                 for wdata in conn.execute(query).fetchall()]
    word_data.sort(key=lambda x: x[4], reverse=True)

    total_r1 = sum([x[1] for x in word_data])
    total_r2 = sum([x[2] for x in word_data])
    total_r3 = sum([x[3] for x in word_data])
    num_words = len(word_data)

    avg_r1 = round(total_r1 / num_words, 1)
    avg_r2 = round(total_r2 / num_words, 1)
    avg_r3 = round(total_r3 / num_words, 1)
    avg_total = round((total_r1 + total_r2 + total_r3) / (3 * num_words), 1)

    word_data.append(("Average", avg_r1, avg_r2, avg_r3, avg_total))

    return word_data


def create_rand_id(n=10) -> str:
    chars = string.ascii_uppercase
    return "".join(random.choice(chars) for _ in range(n))


def bump_player_queue(queue: List[List[str]]) -> List[List[str]]:
    """
    Increment the player queue.

    Queue is input/output as a string rep of a List[List[str]] of player ids. Must be in string format for SQLite
    storage.

    Return the current player, next player, and new queue
    """
    q = copy.deepcopy(queue)
    current_team = q.pop(0)
    current_player = current_team.pop(0)
    current_team.append(current_player)
    q.append(current_team)

    return q

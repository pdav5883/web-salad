import os
import string
import random
import json
from typing import List, Tuple, Union, Dict
import copy
import boto3
import sqlite3
import ast
from collections import defaultdict

from common.model import Entry, Game, Player, Word, Attempt

TABLE_NAME = "web-salad-table"
INDEX_NAME = "gid-type-index"

ddb = boto3.client("dynamodb")


#######################################
# Database Interaction
#######################################

def get_entry_by_id(entry_id: str, entry_type: type) -> Entry:
    """
    Returns None if object does not exist
    """
    res = ddb.get_item(TableName=TABLE_NAME, Key={"id": {"S": entry_id}})

    if "Item" in res:
        return entry_type(**ddb_to_fields(res["Item"]))
    else:
        return None


def entry_exists_by_id(entry_id: str) -> bool:
    res = ddb.get_item(TableName=TABLE_NAME, Key={"id": {"S": entry_id}})

    if "Item" in res:
        return True
    else:
        return False


def entry_exists_by_ojb(entry: Entry) -> bool:
    return entry_exists_by_id(entry.id)


def update_entry(entry: Entry):
    """
    Return True if update successful
    """
    alpha = string.ascii_lowercase
    i = 0

    expr = []
    names = {}
    values = {}

    update_dict = entry.get_ddb_dict()
    id_str = update_dict.pop("id")

    for name, value in update_dict.items():
        nk = "#" + alpha[i]
        vk = ":" + alpha[i+1]

        expr.append(nk + "=" + vk)
        names[nk] = name
        values[vk] = value

        i += 2

    expr = "set " + ", ".join(expr)

    names["#id"] = "id"
    values[":id"] = id_str

    try:
        res = ddb.update_item(TableName=TABLE_NAME,
                              Key={"id": id_str},
                              UpdateExpression=expr,
                              ConditionExpression="#id=:id",
                              ExpressionAttributeNames=names,
                              ExpressionAttributeValues=values)
        return True
    
    except ddb.exceptions.ConditionalCheckFailedException:
        print(f"Update Entry Error: Entry with id {entry.id} does not exist")
        return False


def add_entry(entry: Entry) -> bool:
    """
    Return True if successful
    """
    try:
        res = ddb.put_item(TableName=TABLE_NAME,
                           Item=entry.get_ddb_dict(),
                           ConditionExpression="attribute_not_exists(id)")
        return True
    
    except ddb.exceptions.ConditionalCheckFailedException:
        print(f"Add Entry Error: Entry with id {entry.id} already exists")
        return False


def add_entries(entries: List[Entry]) -> bool:
    """
    Insert a list of entries into the table. Return True if all successful
    """
    success = True

    for entry in entries:
        success = success and add_entry(entry)

    return success

    
def update_entries(entries: List[Entry]) -> bool:
    """
    Update a list of entries in the DB table. Return True if all successful
    """
    success = True

    for entry in entries:
        success = success and update_entry(entry)

    return success


def get_entries_by_gid_type(gid: str, entry_type: type, filters: dict = None) -> List[Entry]:
    """
    Query global index for all entries of specific type

    Optional filters: dict of attr/val equality filters
    """
    query_expr = "#G = :gg AND #T = :tt"
    attr_names = {"#G": "gid", "#T": "type"}
    attr_values = {":gg": {"S": gid}, ":tt": {"S": entry_type.type}}

    if filters:
        filter_expr = []
        alpha = string.ascii_lowercase
        i = 0

        for k, v in to_ddb_format(filters).items():
            nk = "#" + alpha[i]
            vk = ":" + alpha[i+1]

            filter_expr.append(nk + " = " + vk)
            attr_names[nk] = k
            attr_values[vk] = v

            i += 2

        filter_expr = " AND ".join(filter_expr)

        # wrap in kwargs to allow function to work without filters
        # hack is necessary b/c there is no "no filter" arg
        #  for FilterExpression if it is present
        kwargs = {"FilterExpression": filter_expr}

    else:
        kwargs = {}

    res = ddb.query(TableName=TABLE_NAME, IndexName=INDEX_NAME,
                    KeyConditionExpression=query_expr,
                    ExpressionAttributeNames=attr_names,
                    ExpressionAttributeValues=attr_values,
                    **kwargs)

    return [entry_type(**ddb_to_fields(item)) for item in res["Items"]]

        

#######################################
# Back-End Methods
#######################################


def auth_game(gid) -> bool:
    """
    Check for game ID
    """
    if gid:
        return entry_exists_by_id(gid)
    else:
        return False


def auth_player(pid) -> bool:
    """
    Check for player ID
    """
    if pid:
        return entry_exists_by_id(pid)
    else:
        return False


def get_players_by_game_id(gid: str) -> List[Player]:
    """
    Get all the players in this game
    """
    return get_entries_by_gid_type(gid, Player) 


def get_captain_by_game_id(gid: str) -> Player:
    """
    The captain of the game
    """
    game = get_entry_by_id(gid, Game)

    
    if game:
        return get_entry_by_id(game.captain_id, Player)
    else:
        return None


def player_exists_by_name_game_id(gid: str, name: str) -> bool:
    """
    Return whether a player with given name already exists in the game
    """
    if get_entries_by_gid_type(gid, Player, {"name": name}):
        return True
    else:
        return False


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
    game = get_entry_by_id(gid, Game)

    return get_entries_by_gid_type(gid, Word, {"r" + str(game.round) + "_done": False})


def get_attempts_by_game_id(gid: str) -> List[Attempt]:
    """
    All the attempts that have happened in this game
    """
    return get_entries_by_gid_type(gid, Attempt)

#
#def get_scores_by_game_id(gid: str) -> Tuple[int, int]:
#    """
#    Return total scores for team A and team B
#    """
#    attempts_a, attempts_b = get_point_attempts_by_team_by_game_id(gid)
#
#    score_a = score_b = 0
#
#    for attempt in attempts_a:
#        if attempt.success:
#            score_a += 1
#        else:
#            score_b += 1
#
#    for attempt in attempts_b:
#        if attempt.success:
#            score_b += 1
#        else:
#            score_a += 1
#
#    return score_a, score_b


def get_scores_by_round_by_game_id(gid: str) -> Tuple[List[int], List[int]]:
    """
        Return total scores for team A and team B as a list by round
        """
    attempts_a = get_entries_by_gid_type(gid, Attempt, {"team": "a", "point": True})
    attempts_b = get_entries_by_gid_type(gid, Attempt, {"team": "b", "point": True})

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


#######################################
# Common Utilities
#######################################

def create_rand_id(n=10) -> str:
    chars = string.ascii_uppercase
    return "".join(random.choice(chars) for _ in range(n))


def ddb_to_fields(item):
    """
    Convert from DynamoDB dict with types nested to flat dict
    """
    t = {}

    for k, v in item.items():
        for vk in v:
            if vk == "N":
                t[k] = int(v[vk])
            else:
                t[k] = v[vk]

    if "type" in t:
        del t["type"]
    
    return t


def to_ddb_format(from_dict):
    """
    Convert dict to dynamodb format
    {"strkey": strval, "numkey": numval, "boolkey": boolval}
    -->
    {"strkey": {"S": strval}, "numkey": {"N": ...}}
    """
    to_dict = {}

    for k, v in from_dict.items():
        if type(v) in (int, float):
                to_dict[k] = {"N": str(v)}
        elif type(v) == bool:
                to_dict[k] = {"BOOL": v}
        elif type(v) == str:
                to_dict[k] = {"S": v}
        else:
            raise TypeError(f"Invalid type {type(v)} for key {k}")

    return to_dict


def parse_cookies(cookie_str_list):
    """
    Input is cookie_str_list = ["cookie1=val1", "cookie2=val2"]
    """
    return dict(cookie_str.replace(" ","").split("=") for cookie_str in cookie_str_list)



def bump_player_queue(queue: List[List[str]]) -> List[List[str]]:
    """
    Increment the player queue.

    Queue is input/output as a string rep of a List[List[str]] of player ids.

    Return the new queue
    """
    q = copy.deepcopy(queue)
    current_team = q.pop(0)
    current_player = current_team.pop(0)
    current_team.append(current_player)
    q.append(current_team)

    return q

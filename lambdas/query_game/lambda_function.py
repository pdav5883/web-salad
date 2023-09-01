import json

from common import utils
from common import model
from common import _version

"""
Endpoint for 

/getendgame (no args)
/getgame (gid in args)
/getroster (gid in args)
/getscoreboard (gid, pid in args)
/getversion (no args)
"""



def lambda_handler(event, context):
    params = event.get("queryStringParameters", {})

    route = event.get("rawPath", "Missing")

    if route == "/getversion":
        return get_version(params)
    elif route == "/getgame":
        return get_game(params)
    elif route == "/getroster":
        return get_roster(params)
    elif route == "/getscoreboard":
        return get_scoreboard(params)
    elif route == "/getendgame":
        return get_endgame(params)
    else:
        return {"statusCode": 400,
                "body": json.dumps({"message": f"Route is invalid: {route}"})}


def get_version(params):
    data = {"version": _version.__version__}

    return {"statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(data)}
    

def get_game(params):
    """
    Before joining game, see if it exists, and if it is started

    If it exists and is not started
    """
    gid = params.get("gid", None)

    if gid is None:
        return {"statusCode": 400,
                "body": json.dumps({"message": "Missing param gid"})}
        
    game = utils.get_entry_by_id(gid, model.Game)

    if game is None:
        return {"statusCode": 400,
                "body": json.dumps({"message": f"Invalid gid '{gid}'"})}

    if game.started:
        return {"statusCode": 400,
                "body": json.dumps({"message": f"Game with gid '{gid}' has already started"})}

    return {"statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": f"Found game with gid '{gid}'"})}
    

def get_roster(params):
    """
    Return whether games started, list of (name, ready?) tuples for all players,
    gid, am i captain?, captain name
    """
    gid = params.get("gid", None)
    pid = params.get("pid", None)

    if not utils.auth_player(pid):
        return {"statusCode": 400,
                "body": json.dumps({"message": f"Invalid pid '{pid}'"})}

    game = utils.get_entry_by_id(gid, model.Game)

    if game.started:
        return {"statusCode": 200,
                "body": json.dumps({"started": True})}

    players = utils.get_players_by_game_id(gid)
    captain = utils.get_captain_by_game_id(gid)

    names_ready = [(p.name, p.ready) for p in players]
    captain_name = captain.name
    is_captain = (pid == captain.id)

    data = {"started": False, "names_ready": names_ready, "gid": gid,
            "is_captain": is_captain, "captain_name": captain_name}

    return {"statusCode": 200,
            "body": json.dumps(data)}


def get_scoreboard(params):
    """
    Return gameover?, gid, my turn?, game status dict, scores dict, list of tuples of player names 
    """
    gid = params.get("gid", None)
    pid = params.get("pid", None)
    
    if not utils.auth_player(pid):
        return {"statusCode": 400,
                "body": json.dumps({"message": f"Invalid pid '{pid}'"})}
        
    game = utils.get_entry_by_id(gid, model.Game)
    
    if game.complete:
        return {"statusCode": 200,
                "body": json.dumps({"complete": True})}

    curr_id = game.queue[0][0]
    next_id = game.queue[1][0]

    curr_player = utils.get_entry_by_id(curr_id, model.Player)
    next_player = utils.get_entry_by_id(next_id, model.Player)
    num_words_remaining = len(utils.get_words_remaining(gid))

    game_status = {"round": game.round,
                   "curr_player": curr_player.name,
                   "next_player": next_player.name,
                   "num_words": num_words_remaining}

    team_a, team_b = utils.get_teams_by_game_id(gid)

    if len(team_a) > len(team_b):
        team_b.append("")
    teams = list(zip(team_a, team_b))

    scores_a, scores_b = utils.get_scores_by_round_by_game_id(gid)
    scores = {"r1a": scores_a[0] or "-",
              "r1b": scores_b[0] or "-",
              "r2a": scores_a[1] or "-",
              "r2b": scores_b[1] or "-",
              "r3a": scores_a[2] or "-",
              "r3b": scores_b[2] or "-",
              "totala": sum(scores_a),
              "totalb": sum(scores_b)}

    myturn = (pid == curr_id)

    data = {"complete": False, "gid": gid, "myturn": myturn, "status": game_status,
            "scores": scores, "teams": teams}

    return {"statusCode": 200,
            "body": json.dumps(data)}
    

def get_endgame(params):
    pass
    

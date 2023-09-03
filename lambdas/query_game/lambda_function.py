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

    If it exists and is not started return the number of words in game
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
            "body": json.dumps({"message": f"Found game with gid '{gid}'",
                                "numwords": game.words_per_player})}
    

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
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"started": True})}

    players = utils.get_players_by_game_id(gid)
    captain = utils.get_captain_by_game_id(gid)

    names_ready = [(p.name, p.ready) for p in players]
    captain_name = captain.name
    is_captain = (pid == captain.id)

    data = {"started": False, "names_ready": names_ready,
            "is_captain": is_captain, "captain_name": captain_name}

    return {"statusCode": 200,
            "headers": {"Content-Type": "application/json"},
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
                "headers": {"Content-Type": "application/json"},
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

    data = {"complete": False, "myturn": myturn, "status": game_status,
            "scores": scores, "teams": teams}

    return {"statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(data)}
    

def get_endgame(params):
    """
    Return scores and stats to gameover page
    """
    gid = params.get("gid", None)
    pid = params.get("pid", None)
    
    if not utils.auth_player(pid):
        return {"statusCode": 400,
                "body": json.dumps({"message": f"Invalid pid '{pid}'"})}
        
    game = utils.get_entry_by_id(gid, model.Game)
    
    if not game.complete:
        return {"statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"complete": False})}

    scores_a, scores_b = utils.get_scores_by_round_by_game_id(gid)
    scores = {"r1a": scores_a[0],
              "r1b": scores_b[0],
              "r2a": scores_a[1],
              "r2b": scores_b[1],
              "r3a": scores_a[2],
              "r3b": scores_b[2],
              "totala": sum(scores_a),
              "totalb": sum(scores_b)}

    if sum(scores_a) > sum(scores_b):
        winner_str = "Team A Wins!"
    elif sum(scores_a) < sum(scores_b):
        winner_str = "Team B Wins!"
    else:
        winner_str = "Woah, a tie!!"

    teama_stats = get_team_stats(gid, "a")
    teamb_stats = get_team_stats(gid, "b")
    words_stats = get_word_stats(gid)

    mvp_a = teama_stats[0]
    mvp_b = teamb_stats[0]
    if mvp_a[4] > mvp_b[4]:
        mvp_name = mvp_a[0]
    elif mvp_a[4] < mvp_b[4]:
        mvp_name = mvp_b[0]
    else:
        mvp_name = f"{mvp_a[0]}/{mvp_b[0]}"

    stats = {"teama": teama_stats,
             "teamb": teamb_stats,
             "words": words_stats,
             "mvp_name": mvp_name,
             "hardest_word": words_stats[0][0],
             "easiest_word": words_stats[-2][0]}

    data = {"complete": True, "winner_str": winner_str, "scores": scores, "stats": stats}

    return {"statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(data)}


def get_team_stats(gid: str, team: str):
    """
    Return a list of tuples with stats for a full team. Each entry in list corresponds to player. List is sorted by
    total points scored by player. Each tuple contains name str, net r1 score, r2 score int, r3 score int, total score
    int.
    """
    attempts = utils.get_entries_by_gid_type(gid, model.Attempt, {"team": team})
    players = utils.get_entries_by_gid_type(gid, model.Player, {"team": team})

    # dict with pid as key, list of net score for each round is value
    player_data = {player.id: 3 * [0] for player in players}

    for attempt in attempts:
        if not attempt.point:
            continue

        point = 1 if attempt.success else -1
        player_data[attempt.pid][attempt.round - 1] += point

    # need lookup for player name since attempts only include pid
    pid_to_name = {player.id: player.name for player in players}

    player_data_return = []
    for pid, rounds in player_data.items():
        player_data_return.append((pid_to_name[pid], rounds[0], rounds[1], rounds[2], sum(rounds)))

    player_data_return.sort(key=lambda x: x[4], reverse=True)
    return player_data_return


def get_word_stats(gid: str):
    """
    Each entry in list is tuple of word data. Tuple contains word str, r1 time, r2 time, r3 time, avg time. List is
    sorted by avg time. Extra list entry for total avg.
    """
    attempts = utils.get_entries_by_gid_type(gid, model.Attempt)
    words = utils.get_entries_by_gid_type(gid, model.Word)

    word_data = {word.id: 3 * [0] for word in words}

    wid_to_word = {word.id: word.word for word in words} 

    for attempt in attempts:
        word_data[attempt.wid][attempt.round - 1] += attempt.seconds

    word_data_return = []
    for wid, rounds in word_data.items():
        word_data_return.append((wid_to_word[wid], rounds[0], rounds[1], rounds[2], round(sum(rounds) / 3)))

    word_data_return.sort(key=lambda x: x[4], reverse=True)

    # add average row
    total_r1 = sum([x[1] for x in word_data_return])
    total_r2 = sum([x[2] for x in word_data_return])
    total_r3 = sum([x[3] for x in word_data_return])
    num_words = len(word_data_return)

    avg_r1 = round(total_r1 / num_words, 1)
    avg_r2 = round(total_r2 / num_words, 1)
    avg_r3 = round(total_r3 / num_words, 1)
    avg_total = round((total_r1 + total_r2 + total_r3) / (3 * num_words), 1)

    word_data_return.append(("Average", avg_r1, avg_r2, avg_r3, avg_total))

    return word_data_return


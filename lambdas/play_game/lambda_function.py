import json
import random

from common import utils
from common import model
from common import _version

"""
Endpoint for 

/prepareturn (gid, pid in args)
/submitturn [POST] (gid, pid, wids, attempt_point, attempt_success, attempt_durs, time_remaining)
"""


def lambda_handler(event, context):
    params = event.get("queryStringParameters", {})
    body = json.loads(event.get("body", "{}"))

    params = {**params, **body} # combine body and query string since some endpoints use post
    route = event.get("rawPath", "Missing")

    if route == "/prepareturn":
        return prepare_turn(params)
    elif route == "/submitturn":
        return submit_turn(params)
    else:
        return {"statusCode": 400,
                "body": json.dumps({"message": f"Route is invalid: {route}"})}


def prepare_turn(params):
    """
    Returns the wids and words remaining if it is the player's turn
    """
    gid = params.get("gid", None)
    pid = params.get("pid", None)

    if not utils.auth_player(pid):
        return {"statusCode": 400,
                "body": json.dumps({"message": f"Invalid pid {pid}"})}

    game = utils.get_entry_by_id(gid, model.Game)

    # make sure pid matches current turn
    if pid != game.queue[0][0]:
        return {"statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "data": json.dumps({"myturn": False})}

    words = utils.get_words_remaining(gid)
    random.shuffle(words)
    wids = [word.id for word in words]
    word_strs = [word.word for word in words]
    time_remaining = game.time_remaining

    data = {"myturn": True, "gid": gid, "wids": wids, "words": word_strs, "time_remaining": time_remaining}

    return {"statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(data)}


def submit_turn(params):
    """
    Submit words and update scores, update the game

    Did we just end a round? Set time remaining. If not bump the queue
    """
    gid = params.get("gid", None)
    pid = params.get("pid", None)

    if not utils.auth_player(pid):
        return {"statusCode": 400,
                "body": json.dumps({"message": f"Invalid pid {pid}"})}

    game = utils.get_entry_by_id(gid, model.Game)
    player = utils.get_entry_by_id(pid, model.Player)
    
    # make sure pid matches current turn
    if pid != game.queue[0][0]:
        return {"statusCode": 200}

    # retrieve turn data sent in request
    attempt_wids = params["attempt_wids"]
    attempt_point = params["attempt_point"]     # make sure this is parsed as list of bool
    attempt_success = params["attempt_success"] # make sure this is parsed as list of bool
    attempt_durs = params["attempt_durs"]       # make sure this is parsed as list of int
    time_remaining = params["time_remaining"]

    attempts = [model.Attempt(utils.create_rand_id(), wid, pid, gid, game.round, success, point, seconds, player.team)
                for wid, point, success, seconds in zip(attempt_wids, attempt_point, attempt_success, attempt_durs)]
    
    utils.add_entries(attempts)

    # mark words as done for this round
    for wid, point in zip(attempt_wids, attempt_point):
        if point:
            word = utils.get_entry_by_id(wid, model.Word)
            setattr(word, f"r{game.round}_done", True)
            utils.update_entry(word)

    if time_remaining > 0:
        # the game is over!
        if game.round == 3:
            game.complete = True
            game.queue = [[None], [None]]

        # move to the next round, same person's turn with the balance of their time multiplied by ratio of round times
        else:
            time_prev_round = getattr(game, f"r{game.round}_sec")
            time_next_round = getattr(game, f"r{game.round + 1}_sec")
            game.round += 1
            game.time_remaining = int(time_remaining * time_next_round / time_prev_round)

    else:
        game.time_remaining = getattr(game, f"r{game.round}_sec")
        game.queue = utils.bump_player_queue(game.queue)

    utils.update_entry(game)

    return {"statusCode": 200}



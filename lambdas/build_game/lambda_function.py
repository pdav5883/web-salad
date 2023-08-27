import json

from common import utils
from common import model
from common import _version

"""
Endpoint for 

/submitgame (gid, num words, round times in args)
/submitplayer (name in args, gid in cookie)
/submitwords (word list in args, gid/pid in cookie)
/preparegame [POST] (form data, gid/pid in cookie)
"""


def lambda_handler(event, context):
    params = event.get("queryStringParameters", {})
    body = event.get("body", {})
    cookies = utils.parse_cookies(event.get("cookies", {}))

    params = {**params, **body} # combine body and query string since some endpoints use post
    route = event.get("rawPath", "Missing")

    if route == "/submitgame":
        return submit_game(params, cookies)
    elif route == "/submitplayer":
        return submit_player(params, cookies)
    elif route == "/submitwords":
        return submit_words(params, cookies)
    elif route == "/preparegame":
        return prepare_game(params, cookies)
    else:
        return {"statusCode": 400,
                "body": json.dumps({"message": f"Route is invalid: {route}"})}


def submit_game(params, cookies):
    """
    Create a new game with the params provided in request
    """
    try:
        new_gid = params.get("new_gid")
        num_words = params.get("num_words")
        t1 = params.get("t1")
        t2 = params.get("t2")
        t3 = params.get("t3")

    except KeyError:
        msg = "Missing parameter: request must contain new_gid, num_words, t1, t2, t3"
        return {"statusCode": 400,
                "body": json.dumps({"message": msg})}

    new_game = model.Game(new_gid, num_words, t1, t2, t3)

    if utils.add_entry(new_game):
        return {"statusCode": 200}
    else:
        return {"statusCode": 400,
                "body": json.dumps({"message": f"Could not add new gid {new_gid}"})}
    

def submit_player(params, cookies):
    """
    Add player to game. gid in cookies, player name in request
    """
    gid = cookies.get("gid", None)

    if not utils.auth_game(gid):
        return {"statusCode": 400,
                "body": json.dumps({"message": f"Invalid gid {gid}"})}

    pname = params.get("pname", None)
    
    if not pname:
        return {"statusCode": 400,
                "body": json.dumps({"message": "No player name present"})}

    if utils.player_exists_by_name_game_id(gid, pname):
        return {"statusCode": 400,
                "body": json.dumps({"message": f"Player name {pname} already used"})}

    player = model.Player(utils.create_rand_id(), gid, pname)
    utils.add_entry(player)

    # if this is the first player, assign them captain
    game = utils.get_entry_by_id(gid, model.Game)
    if game.captain_id is None:
        game.captain_id = player.id
        utils.update_entry(game)

    return {"statusCode": 200,
            "cookies": [f"pid={player.id}"]}

   
def submit_words(params, cookies):
    """
    Add a player's words to game

    After testing with ajax, it looks like array will get passed as words[]: "w1,w2,w3"
    """
    gid = cookies.get("gid", None)
    pid = cookies.get("pid", None)

    if not utils.auth_player(pid):
        return {"statusCode": 400,
                "body": json.dumps({"message": f"Invalid pid {pid}"})}

    if "words[]" in params:
        words = params.get("words[]").split(",")
    elif "words" in params:
        words = params.get("words").split(",")
    else:
        return {"statusCode": 400,
                "body": json.dumps({"message": f"Missing words parameter"})}

    utils.add_entries([model.Word(utils.create_rand_id(), pid, gid, word) for word in words])

    return {"statusCode": 200}


def prepare_game(params, cookies):
    data = {}

    return {"statusCode": 200,
            "body": json.dumps(data)}
    


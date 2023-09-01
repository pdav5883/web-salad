import json
import random
import itertools

from common import utils
from common import model
from common import _version

"""
Endpoint for 

/submitgame (gid, num words, round times in args)
/submitplayer (gid, name in args)
/submitwords (gid, pid, word list in args)
/preparegame [POST] (gid, pid, form data)
"""


def lambda_handler(event, context):
    params = event.get("queryStringParameters", {})
    body = json.loads(event.get("body", "{}"))

    params = {**params, **body} # combine body and query string since some endpoints use post
    route = event.get("rawPath", "Missing")

    if route == "/submitgame":
        return submit_game(params)
    elif route == "/submitplayer":
        return submit_player(params)
    elif route == "/submitwords":
        return submit_words(params)
    elif route == "/preparegame":
        return prepare_game(params)
    else:
        return {"statusCode": 400,
                "body": json.dumps({"message": f"Route is invalid: {route}"})}


def submit_game(params):
    """
    Create a new game with the params provided in request
    """
    try:
        new_gid = params["new_gid"]
        num_words = params["num_words"]
        t1 = params["t1"]
        t2 = params["t2"]
        t3 = params["t3"]

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
    

def submit_player(params):
    """
    Add player to game. gid, player name in request
    """
    gid = params.get("gid", None)

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
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"pid": player.id})}

   
def submit_words(params):
    """
    Add a player's words to game

    After testing with ajax, it looks like array will get passed as words[]: "w1,w2,w3"
    """
    gid = params.get("gid", None)
    pid = params.get("pid", None)

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

    # update player to ready
    player = utils.get_entry_by_id(pid, model.Player)
    player.ready = True
    utils.update_entry(player)

    return {"statusCode": 200}


def prepare_game(params):
    """
    Builds the teams and starts game. Only the captain can submit. Returns goto parameter telling
    the client where to go next: "roster" or "scoreboard" on success
    """
    gid = params.get("gid", None)
    pid = params.get("pid", None)

    if not utils.auth_player(pid):
        return {"statusCode": 400,
                "body": json.dumps({"message": f"Invalid pid {pid}"})}

    game = utils.get_entry_by_id(gid, model.Game)
    players = utils.get_players_by_game_id(gid)
    this_player = utils.get_entry_by_id(pid, model.Player)

    if game.started:
        return {"statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"goto": "scoreboard"})}

    if game.captain_id != this_player.id:
        return {"statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"goto": "roster",
                                    "message": "You are not the captain"})}

    # don't let the game start with just one player
    if len(players) <= 1:
        return {"statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"goto": "roster",
                                    "message": "Wait for another player"})}

    # don't let the game start if everyone not ready
    if not all([player.ready for player in players]):
        return {"statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"goto": "roster",
                                    "message": "Not everyone is ready"})}
 
    name_list = params.get("name_list")
    group_list = params.get("group_list")
    names_groups = list(zip(name_list, group_list))

    # constraint dict references names in
    constraints = {}
    for i, (name_i, group_i) in enumerate(names_groups):
        if not group_i:
            continue
        for j, (name_j, group_j) in enumerate(names_groups):
            if i != j and group_i == group_j:
                constraints[name_i] = name_j
                break

    # need to keep a list of player references to update DB later
    players_post = list(players)
    players_by_name = {player.name: player for player in players}
    random.shuffle(players)

    # assign teams and enforce constraint that two players with same
    # group label end up on different teams
    teams_id = {"a": [], "b": []}
    teams_name = {"a": [], "b": []}
    a_b = itertools.cycle(["a", "b"]) 

    while len(players):
        team = next(a_b)
        player = players.pop()
        player.team = team
        teams_id[team].append(player.id)
        teams_name[team].append(player.name)

        if player.name in constraints:
            other_team = next(a_b)
            other_player = players_by_name[constraints[player.name]]
            other_player.team = other_team
            teams_id[other_team].append(other_player.id)
            teams_name[other_team].append(other_player.name)

            del constraints[player.name]
            del constraints[other_player.name]
            players.remove(other_player)

    # set up the game
    game.started = True
    game.queue = [teams_id["b"], teams_id["a"]]
    game.round = 1
    game.time_remaining = game.r1_sec

    utils.update_entry(game)
    utils.update_entries(players_post)

    return {"statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"goto": "scoreboard"})}


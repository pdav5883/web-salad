import string
import random
import json

from flask import Flask, render_template, url_for, redirect, request, make_response



gpath = "data/games.txt"
ppath = "data/players.txt"
wpath = "data/words.txt"

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/admin/")
def admin():
    # auth the admin
    return render_template("admin.html")


@app.route("/addgame/")
def add_game():
    new_gid = request.args.get("new_gid", None)
    num_words = request.args.get("num_words", 5)
    t1 = request.args.get("t1", 30)
    t2 = request.args.get("t2", 30)
    t3 = request.args.get("t3", 30)

    data = {"gid": new_gid, "num_words": num_words, "t1": t1, "t2": t2, "t3": t3}

    if new_gid:
        with open(gpath, "a") as fptr:
            fptr.write(f"{json.dumps(data)}\n")

        return redirect(url_for("home"))
    else:
        return redirect(url_for("admin"))


@app.route("/joingame/")
def join_game():
    gid = request.args.get("gid", None)
    if gid and check_game_id(gid):
        resp = make_response(redirect(url_for("new_player")))
        resp.set_cookie("gid", gid)
        return resp
    else:
        return redirect(url_for("bad"))


@app.route("/newplayer/")
def new_player():
    # maybe check to make sure a player doesn't already exist in cookies to stop one user creating multiple players
    if not auth_game(request):
        return redirect(url_for("bad"))
    return render_template("newplayer.html")


@app.route("/submitplayer/")
def submit_player():
    if not auth_game(request):
        return redirect(url_for("bad"))

    pname = request.args.get("pname", None)
    if not pname:
        return redirect(url_for("submit_player"))

    pid = create_rand_id()

    data = {"pid": pid, "pname": pname}

    with open(ppath, "a") as fptr:
        fptr.write(f"{json.dumps(data)}\n")

    resp = make_response(redirect(url_for("new_words")))
    resp.set_cookie("pid", pid)
    return resp


@app.route("/newwords/")
def new_words():
    if not auth_player(request):
        return redirect(url_for("bad"))

    gid = request.cookies.get("gid")
    game = get_game(gid)

    return render_template("newwords.html", num_words=game["num_words"])


@app.route("/submitwords/")
def submit_words():
    if not auth_player(request):
        return redirect(url_for("bad"))

    words = request.args.getlist("words[]")

    # TODO: do something if not all words are filled in?

    with open(wpath, "a") as fptr:
        for word in words:
            fptr.write(f"{word}\n")
    return redirect(url_for("good"))


@app.route("/bad/")
def bad():
    return "You messed up :("


@app.route("/good/")
def good():
    return "Good job :)"


def check_game_id(gid):
    """
    Check game ID string against db
    """
    games = get_games()
    game_ids = [game["gid"] for game in games]

    if gid in game_ids:
        return True
    else:
        return False


def check_player_id(pid):
    """
    Check player ID string against db
    """
    players = get_players()
    player_ids = [player["pid"] for player in players]

    if pid in player_ids:
        return True
    else:
        return False


def create_rand_id(n=10):
    chars = string.ascii_uppercase
    return "".join(random.choice(chars) for _ in range(n))


def auth_game(req):
    """
    Check cookies for game ID
    """
    gid = req.cookies.get("gid", None)
    if gid:
        return check_game_id(gid)
    else:
        return False


def auth_player(req):
    """
    Check cookies for valid player ID
    """
    pid = req.cookies.get("pid", None)
    if pid:
        return check_player_id(pid)
    else:
        return False


def get_games():
    with open(gpath, "r") as fptr:
        rows = fptr.read().splitlines()

    return [json.loads(row) for row in rows if row]


def get_players():
    with open(ppath, "r") as fptr:
        rows = fptr.read().splitlines()

    return [json.loads(row) for row in rows if row]


def get_game(gid):
    games = get_games()

    for game in games:
        if game["gid"] == gid:
            return game
    return None


def get_player(pid):
    players = get_players()

    for player in players:
        if player["pid"] == pid:
            return player
    return None

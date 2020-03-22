from flask import Flask, render_template, url_for, redirect, request

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

    if new_gid:
        with open(gpath, "a") as fptr:
            fptr.write(f"{new_gid}\n")

        return redirect(url_for("home"))
    else:
        return redirect(url_for("admin"))


@app.route("/joingame/")
def join_game():
    gid = request.args.get("gid", None)
    if gid and check_game(gid):
        return redirect(url_for("new_player"))
    else:
        return redirect(url_for("bad"))


def check_game(gid):
    with open(gpath, "r") as fptr:
        games = fptr.read().split()

    if gid in games:
        return True
    else:
        return False


@app.route("/newplayer/")
def new_player():
    # auth the game id
    return render_template("newplayer.html")


@app.route("/submitplayer/")
def submit_player():
    # do some stuff to create the player
    with open(ppath, "a") as fptr:
        fptr.write(f"{request.args.get('pname', 'failed')}\n")
    return redirect(url_for("new_words"))


@app.route("/newwords/")
def new_words():
    return render_template("newwords.html")


@app.route("/submitwords/")
def submit_words():
    # do some stuff to store words
    with open(wpath, "a") as fptr:
        fptr.write(f"{request.args.get('word1', 'failed')}\n")
        fptr.write(f"{request.args.get('word2', 'failed')}\n")
    return redirect(url_for("good"))


@app.route("/bad/")
def bad():
    return "You messed up :("


@app.route("/good/")
def good():
    return "Good job :)"

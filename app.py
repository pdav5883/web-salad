from flask import Flask, render_template, url_for, redirect, request

gpath = "data/games.txt"
ppath = "data/names.txt"
wpath = "data/words.txt"

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/joingame/")
def join_game():
    gid = request.args.get("gid", "0")
    if check_game(gid):
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
    with open(ppath, "w") as fptr:
        fptr.write(request.args.get("pname", "failed"))
    return redirect(url_for("new_words"))


@app.route("/newwords/")
def new_words():
    return render_template("newwords.html")


@app.route("/submitwords/")
def submit_words():
    # do some stuff to store words
    with open(wpath, "w") as fptr:
        fptr.write(request.args.get("word1", "failed"))
        fptr.write("\n")
        fptr.write(request.args.get("word2", "failed"))
    return redirect(url_for("good"))


@app.route("/bad/")
def bad():
    return "Whoops!"


@app.route("/good/")
def good():
    return "OK!"

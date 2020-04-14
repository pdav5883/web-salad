from random import shuffle
from itertools import cycle

from flask import Flask, render_template, url_for, redirect, request, make_response

from model import Game, Player, Word, Attempt
from utils import *

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/admin/")
def admin():
    # auth the admin
    return render_template("admin.html")


@app.route("/submitgame/")
def submit_game():
    new_gid = request.args.get("new_gid")
    num_words = request.args.get("num_words")
    t1 = request.args.get("t1")
    t2 = request.args.get("t2")
    t3 = request.args.get("t3")

    new_game = Game(new_gid, num_words, t1, t2, t3)

    gdata = {"num_words": num_words, "t1": t1, "t2": t2, "t3": t3, "started": False}

    if add_entry(new_game):
        return redirect(url_for("home"))
    else:
        return redirect(url_for("admin"))


@app.route("/joingame/")
def join_game():
    gid = request.args.get("gid", None)

    if gid is None:
        return redirect(url_for("bad"))

    game: Game = get_entry_by_id(gid, Game)

    if game is None:
        return redirect(url_for("bad"))

    if game.started:
        return redirect(url_for("bad"))

    resp = make_response(redirect(url_for("new_player")))
    resp.set_cookie("gid", gid)
    return resp


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

    gid = request.cookies.get("gid")
    pname = request.args.get("pname", None)

    if not pname:
        return redirect(url_for("submit_player"))

    new_pid = create_rand_id()

    # if this is the first player, assign them captain
    if len(get_players_by_game_id(gid)) == 0:
        game = get_entry_by_id(gid, Game)
        game.captain_name = pname
        update_entry(game)

    player = Player(new_pid, gid, pname)
    add_entry(player)

    resp = make_response(redirect(url_for("new_words")))
    resp.set_cookie("pid", new_pid)
    return resp


@app.route("/newwords/")
def new_words():
    if not auth_player(request):
        return redirect(url_for("bad"))

    gid = request.cookies.get("gid")
    game = get_entry_by_id(gid, Game)

    return render_template("newwords.html", num_words=game.words_per_player)


@app.route("/submitwords/")
def submit_words():
    if not auth_player(request):
        return redirect(url_for("bad"))

    words = request.args.getlist("words[]")
    gid = request.cookies.get("gid")
    pid = request.cookies.get("pid")

    add_entries([Word(create_rand_id(), pid, gid, word) for word in words])

    return redirect(url_for("wait_for_players"))


@app.route("/roster/")
def wait_for_players():
    if not auth_player(request):
        return redirect(url_for("bad"))

    gid = request.cookies.get("gid")
    pid = request.cookies.get("pid")

    players = get_players_by_game_id(gid)
    player_captain = [player for player in players if player.captain].pop()

    player_names = [player.name for player in players]
    captain_name = player_captain.name

    is_captain = (pid == player_captain.id)

    return render_template("roster.html", names=player_names, captain=is_captain, captain_name=captain_name)


@app.route("/preparegame/")
def prepare_game():
    if not auth_player(request):
        return redirect(url_for("bad"))

    gid = request.cookies.get("gid")
    pid = request.cookies.get("pid")

    game: Game = get_entry_by_id(gid, Game)
    this_player: Player = get_entry_by_id(pid, Player)

    if game.started:
        return redirect(url_for("scoreboard"))

    if not this_player.captain:
        return redirect(url_for("wait_for_players"))

    # assign teams
    players = get_players_by_game_id(gid)
    teams_id = {"a": [], "b": []}
    teams_name = {"a": [], "b": []}
    a_b = cycle(["a", "b"])
    shuffle(players)
    for player in players:
        team = next(a_b)
        player.team = team
        teams_id[team].append(player.id)
        teams_name[team].append(player.name)

    # set up the game
    game.started = True
    queue = bump_player_queue([teams_id["a"], teams_id["b"]])
    game.queue = queue
    game["team_a"] = teams_name["a"]
    game["team_b"] = teams_name["b"]
    game.score_a = 0
    game.score_b = 0
    game.round = 1
    game["num_remaining"] = len(get_words_remaining())
    game.time_remaining = game.r1_sec

    update_games(games)
    update_players(players)

    return redirect(url_for("scoreboard"))


@app.route("/scoreboard/")
def scoreboard():
    game = get_game(request.cookies.get("gid"))

    if game["complete"]:
        return redirect(url_for("game_over"))

    curr_name = get_player_name(game["curr_id"])
    next_name = get_player_name(game["next_id"])
    my_turn = (request.cookies.get("pid") == game["curr_id"])

    return render_template("scoreboard.html",
                           round=game["round"],
                           curr_name=curr_name,
                           next_name=next_name,
                           my_turn=my_turn,
                           score_a=game["score_a"],
                           score_b=game["score_b"],
                           names_a=game["team_a"],
                           names_b=game["team_b"],
                           words_remaining=game["num_remaining"])


@app.route("/myturn/")
def my_turn():
    # TODO: need some sort of check so that you can only get here when it's your turn hasn't started yet
    word_pairs = get_words_remaining()
    shuffle(word_pairs)
    wids, words = map(list, zip(*word_pairs))
    time_remaining = get_time_remaining(request.cookies.get("gid")
                                        )
    return render_template("myturn.html",
                           wids=json.dumps(wids),
                           words=json.dumps(words),
                           time_remaining=time_remaining)


@app.route("/submitturn/", methods=["POST"])
def submit_turn():
    # submit words and update scores
    # update the game
    # did we just end a round, then go to /endround and set time remaining
    # if not then bump the queue, set time and go to /scoreboard
    correct_wids = request.form.getlist("correct_wids")
    miss_wids = request.form.getlist("miss_wids")
    time_remaining = request.form.get("time_remaining")

    games = get_games()
    game = games[request.cookies.get("gid")]
    player = get_player(request.cookies.get("pid"))
    active_team = player["team"]
    inactive_team = "a" if active_team == "b" else "b"
    words = get_words()

    game[f"score_{active_team}"] += len(correct_wids)
    game[f"score_{inactive_team}"] += len(miss_wids)

    for wid in correct_wids + miss_wids:
        words[wid]["used"] = True

    if int(time_remaining) > 0:
        # the game is over!
        if game["round"] == 3:
            game["complete"] = True

        # move to the next round, same person's turn with the balance of their time
        else:
            game["round"] += 1
            words = reset_words(words)
            game["time_remaining"] = time_remaining
            game["num_remaining"] = len(words)

    else:
        game["curr_id"], game["next_id"], game["queue"] = bump_player_queue(game["queue"])
        game["time_remaining"] = game[f"t{game['round']}"]
        game["num_remaining"] -= len(correct_wids + miss_wids)

    update_games(games)
    update_words(words)

    return redirect(url_for("scoreboard"))


@app.route("/gameover")
def game_over():
    game = get_game(request.cookies.get("gid"))

    if game["score_a"] > game["score_b"]:
        winner_str = "Congratulations Team A!"
        game["winner"] = "a"
    elif game["score_a"] < game["score_b"]:
        winner_str = "Congratulations Team B!"
        game["winner"] = "b"
    else:
        winner_str = "Woah, a tie!!"
        game["winner"] = None

    return render_template("gameover.html",
                           winner_str=winner_str,
                           score_a=game["score_a"],
                           score_b=game["score_b"],
                           names_a=game["team_a"],
                           names_b=game["team_b"]
                           )


@app.route("/bad/")
def bad():
    return "You're not allowed here :("


@app.route("/good/")
def good():
    return "Good job :)"

@app.route("/test/")
def test():
    word_pairs = get_words_remaining()
    shuffle(word_pairs)
    wids, words = map(list, zip(*word_pairs))
    return render_template("myturn.html",
                           wids=json.dumps(wids),
                           words=json.dumps(words),
                           time_remaining=10)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)

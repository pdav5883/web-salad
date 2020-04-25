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

    player = Player(create_rand_id(), gid, pname)
    add_entry(player)

    # if this is the first player, assign them captain
    game = get_entry_by_id(gid, Game)
    if game.captain_id is None:
        game.captain_id = player.id
        update_entry(game)

    resp = make_response(redirect(url_for("new_words")))
    resp.set_cookie("pid", player.id)
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
    captain = get_captain_by_game_id(gid)

    player_names = [player.name for player in players]
    captain_name = captain.name

    is_captain = (pid == captain.id)

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

    if game.captain_id != this_player.id:
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
    game.queue = [teams_id["b"], teams_id["a"]]
    game.round = 1
    game.time_remaining = game.r1_sec

    update_entry(game)
    update_entries(players)

    return redirect(url_for("scoreboard"))


@app.route("/scoreboard/")
def scoreboard():
    if not auth_player(request):
        return redirect(url_for("bad"))

    gid = request.cookies.get("gid")
    pid = request.cookies.get("pid")
    game: Game = get_entry_by_id(gid, Game)

    if game.complete:
        return redirect(url_for("game_over"))

    curr_id = game.queue[0][0]
    next_id = game.queue[1][0]

    curr_player = get_entry_by_id(curr_id, Player)
    next_player = get_entry_by_id(next_id, Player)
    my_turn = (pid == curr_player.id)

    team_a, team_b = get_teams_by_game_id(gid)
    score_a, score_b = get_scores_by_game_id(gid)

    num_words_remaining = len(get_words_remaining(gid))

    return render_template("scoreboard.html",
                           round=game.round,
                           curr_name=curr_player.name,
                           next_name=next_player.name,
                           my_turn=my_turn,
                           score_a=score_a,
                           score_b=score_b,
                           names_a=team_a,
                           names_b=team_b,
                           words_remaining=num_words_remaining)


@app.route("/myturn/")
def my_turn():
    if not auth_player(request):
        return redirect(url_for("bad"))

    gid = request.cookies.get("gid")
    pid = request.cookies.get("pid")
    game: Game = get_entry_by_id(gid, Game)

    # make sure pid matches current turn
    if pid != game.queue[0][0]:
        return redirect(url_for("scoreboard"))

    words = get_words_remaining(gid)
    shuffle(words)
    wids = [word.id for word in words]
    word_strs = [word.word for word in words]
    time_remaining = game.time_remaining

    return render_template("myturn.html",
                           wids=json.dumps(wids),
                           words=json.dumps(word_strs),
                           time_remaining=time_remaining)


@app.route("/submitturn/", methods=["POST"])
def submit_turn():
    # submit words and update scores
    # update the game
    # did we just end a round, then go to /endround and set time remaining
    # if not then bump the queue, set time and go to /scoreboard
    if not auth_player(request):
        return redirect(url_for("bad"))

    gid = request.cookies.get("gid")
    pid = request.cookies.get("pid")
    game: Game = get_entry_by_id(gid, Game)

    # make sure pid matches current turn
    if pid != game.queue[0][0]:
        return redirect(url_for("scoreboard"))

    # retrieve from JS generated html form, must convert correct and durs since they come in as str
    attempt_wids = request.form.getlist("attempt_wids")
    attempt_correct = [json.loads(att_str) for att_str in request.form.getlist("attempt_correct")]
    attempt_durs = [int(att_str) for att_str in request.form.getlist("attempt_durs")]
    time_remaining = int(request.form.get("time_remaining"))

    attempts = [Attempt(create_rand_id(), wid, pid, gid, game.round, success, seconds)
                for wid, success, seconds in zip(attempt_wids, attempt_correct, attempt_durs)]
    add_entries(attempts)

    if time_remaining > 0:
        # the game is over!
        if game.round == 3:
            game.complete = True
            game.queue = [[None], [None]]

        # move to the next round, same person's turn with the balance of their time
        else:
            game.round += 1
            game.time_remaining = time_remaining

    else:
        game.time_remaining = game.__getattribute__(f"r{game.round}_sec")
        game.queue = bump_player_queue(game.queue)

    update_entry(game)

    return redirect(url_for("scoreboard"))


@app.route("/gameover")
def game_over():
    if not auth_player(request):
        return redirect(url_for("bad"))

    gid = request.cookies.get("gid")
    game: Game = get_entry_by_id(gid, Game)

    if not game.complete:
        return redirect(url_for("bad"))

    score_a, score_b = get_scores_by_game_id(gid)
    names_a, names_b = get_teams_by_game_id(gid)

    if score_a > score_b:
        winner_str = "Congratulations Team A!"
    elif score_a < score_b:
        winner_str = "Congratulations Team B!"
    else:
        winner_str = "Woah, a tie!!"

    mvp_name, mvp_points, hardest_word, hardest_time, easiest_word, easiest_time = get_game_stats(gid)

    return render_template("gameover.html",
                           winner_str=winner_str,
                           score_a=score_a,
                           score_b=score_b,
                           names_a=names_a,
                           names_b=names_b,
                           mvp_name=mvp_name,
                           mvp_points=mvp_points,
                           hardest_word=hardest_word,
                           hardest_time=hardest_time,
                           easiest_word=easiest_word,
                           easiest_time=easiest_time
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

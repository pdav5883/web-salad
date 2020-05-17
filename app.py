from random import shuffle
from itertools import cycle

from flask import Flask, render_template, url_for, redirect, request, make_response

from _version import __version__
from utils import *

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html", version=__version__)


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
    return render_template("newplayer.html", gid=request.cookies.get("gid"))


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

    return render_template("newwords.html", num_words=game.words_per_player, gid=gid)


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

    game: Game = get_entry_by_id(gid, Game)
    if game.started:
        return redirect(url_for("scoreboard"))

    players = get_players_by_game_id(gid)
    captain = get_captain_by_game_id(gid)

    player_ids = [player.id for player in players]

    player_names = [player.name for player in players]
    player_status = get_players_ready_by_game_id(gid, player_ids)
    names_ready = list(zip(player_names, player_status))

    captain_name = captain.name
    is_captain = (pid == captain.id)

    return render_template("roster.html", gid=gid, names_ready=names_ready, is_captain=is_captain, captain_name=captain_name)


@app.route("/preparegame/", methods=["POST"])
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

    name_list = request.form.getlist("name_list")
    group_list = request.form.getlist("group_list")
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

    players = get_players_by_game_id(gid)
    players_post = list(players)
    players_by_name = {player.name: player for player in players}
    shuffle(players)

    # assign teams and enforce constraint that two players with same
    # group label end up on different teams
    teams_id = {"a": [], "b": []}
    teams_name = {"a": [], "b": []}
    a_b = cycle(["a", "b"])

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

    update_entry(game)
    update_entries(players_post)

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
    num_words_remaining = len(get_words_remaining(gid))
    status = {"round": game.round,
              "curr_player": curr_player.name,
              "next_player": next_player.name,
              "num_words": num_words_remaining}

    team_a, team_b = get_teams_by_game_id(gid)
    if len(team_a) > len(team_b):
        team_b.append("")
    teams = list(zip(team_a, team_b))

    scores_a, scores_b = get_scores_by_round_by_game_id(gid)
    scores = {"r1a": scores_a[0] or "-",
              "r1b": scores_b[0] or "-",
              "r2a": scores_a[1] or "-",
              "r2b": scores_b[1] or "-",
              "r3a": scores_a[2] or "-",
              "r3b": scores_b[2] or "-",
              "totala": sum(scores_a),
              "totalb": sum(scores_b)}

    myturn = (pid == curr_player.id)

    return render_template("scoreboard.html",
                           gid=gid,
                           myturn=myturn,
                           status=status,
                           scores=scores,
                           teams=teams)


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
                           gid=gid,
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

        # move to the next round, same person's turn with the balance of their time multiplied by ratio of round times
        else:
            time_prev_round = game.__getattribute__(f"r{game.round}_sec")
            time_next_round = game.__getattribute__(f"r{game.round + 1}_sec")
            game.round += 1
            game.time_remaining = int(time_remaining * time_next_round / time_prev_round)

    else:
        game.time_remaining = game.__getattribute__(f"r{game.round}_sec")
        game.queue = bump_player_queue(game.queue)

    update_entry(game)

    return redirect(url_for("scoreboard"))


@app.route("/gameover/")
def game_over():
    if not auth_player(request):
        return redirect(url_for("bad"))

    gid = request.cookies.get("gid")
    game: Game = get_entry_by_id(gid, Game)

    if not game.complete:
        return redirect(url_for("bad"))

    scores_a, scores_b = get_scores_by_round_by_game_id(gid)
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

    return render_template("gameover.html",
                           gid=gid,
                           winner_str=winner_str,
                           scores=scores,
                           stats=stats)


@app.route("/bad/")
def bad():
    return "You're not allowed here :("


@app.route("/good/")
def good():
    return "Good job :)"


@app.route("/test-roster/")
def test_roster():
    gid = "Applesauce"
    names_ready = [("Peter", True),
                   ("Kelly", True),
                   ("Matt", False),
                   ("Molly", True),
                   ("Emily", False),
                   ("Juan", True)]
    is_captain = True
    captain_name = "Peter"

    return render_template("roster.html", gid=gid, names_ready=names_ready, is_captain=is_captain, captain_name=captain_name)


@app.route("/test-scoreboard/")
def test_scoreboard():
    gid = "Applesauce"
    teams = [("Peter", "Kelly"),
             ("Matt", "Molly"),
             ("Juan", "Emily"),
             ("Gio", "Miz")]

    scores = {"r1a": 3 or "-",
              "r1b": 7 or "-",
              "r2a": 4 or "-",
              "r2b": 2 or "-",
              "r3a": 0 or "-",
              "r3b": 0 or "-",
              "totala": 7,
              "totalb": 9}

    status = {"round": 2,
              "curr_player": "Miz",
              "next_player": "Gio",
              "num_words": 4}
    myturn = False

    return render_template("scoreboard.html",
                           gid=gid,
                           myturn=myturn,
                           status=status,
                           scores=scores,
                           teams=teams)

@app.route("/test-gameover/")
def test_gameover():
    gid = "Applesauce"
    teams = [("Peter", "Kelly"),
             ("Matt", "Molly"),
             ("Juan", "Emily"),
             ("Gio", "Miz")]

    scores = {"r1a": 3 or "-",
              "r1b": 7 or "-",
              "r2a": 4 or "-",
              "r2b": 6 or "-",
              "r3a": 10 or "-",
              "r3b": 0 or "-",
              "totala": 17,
              "totalb": 13}

    winner = "A"

    stats_teama = [("Peter", 3, 6, 1, 10),
                   ("Matt", 3, 6, 2, 11),
                   ("Juan", 3, 6, 3, 12),
                   ("Gio", 3, 6, 4, 13),
                   ("Total", 12, 24, 6, 17)]
    stats_teamb = [("Kelly", 3, 6, 1, 10),
                   ("Molly", 3, 6, 2, 11),
                   ("Emily", 3, 6, 3, 12),
                   ("Miz", 3, 6, 4, 13),
                   ("Total", 12, 24, 6, 10)]
    words = [("Dingleberry", 1, 2, 3, 2),
             ("Apple", 5, 6, 77, 6),
             ("Bear", 3, 5, 4, 33),
             ("Bailey", 1, 2, 4, 2),
             ("Average", 4, 3, 4, 3)]

    stats = {"mvp_name": "Kelly",
             "mvp_points": 10,
             "hardest_word": "Dingleberry",
             "hardest_time": 10.5,
             "easiest_word": "Alex Ovechkin",
             "easiest_time": 3,
             "teama": stats_teama,
             "teamb": stats_teamb,
             "words": words
             }

    return render_template("gameover.html",
                           gid=gid,
                           winner=winner,
                           scores=scores,
                           stats=stats)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)

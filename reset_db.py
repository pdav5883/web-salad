import sqlite3

import model

dbpath = "data/salad.db"

conn = sqlite3.connect(dbpath)

# drop existing tables
conn.execute("DROP TABLE IF EXISTS attempt")
conn.execute("DROP TABLE IF EXISTS word")
conn.execute("DROP TABLE IF EXISTS player")
conn.execute("DROP TABLE IF EXISTS game")
conn.commit()

# dictionaries with key attributes and value typing class
game_attr = dict(model.Game.__annotations__)
player_attr = dict(model.Player.__annotations__)
word_attr = dict(model.Word.__annotations__)
attempt_attr = dict(model.Attempt.__annotations__)


def map_col_type(typ):
    if typ == str:
        return "TEXT"
    elif typ == int:
        return "INTEGER"
    elif typ == bool:
        return "INTEGER"
    else:
        return "TEXT"


# start building table creation strings
game_str = "CREATE TABLE game("
player_str = "CREATE TABLE player("
word_str = "CREATE TABLE word("
attempt_str = "CREATE TABLE attempt("

# add columns
for col, typ in game_attr.items():
    game_str += f"{col} {map_col_type(typ)}, "

for col, typ in player_attr.items():
    player_str += f"{col} {map_col_type(typ)}, "

for col, typ in word_attr.items():
    word_str += f"{col} {map_col_type(typ)}, "

for col, typ in attempt_attr.items():
    attempt_str += f"{col} {map_col_type(typ)}, "

# add key constraints
game_str += "PRIMARY KEY(gid))"

player_str += "PRIMARY KEY(pid), " \
              "FOREIGN KEY(gid) REFERENCES game(gid))"

word_str += "PRIMARY KEY(wid), " \
            "FOREIGN KEY(pid) REFERENCES player(pid), " \
            "FOREIGN KEY(gid) REFERENCES game(gid))"

attempt_str += "PRIMARY KEY(aid), " \
               "FOREIGN KEY(wid) REFERENCES word(wid), " \
               "FOREIGN KEY(pid) REFERENCES player(pid), " \
               "FOREIGN KEY(gid) REFERENCES game(gid))"

# repopulate tables
conn.execute(game_str)
conn.execute(player_str)
conn.execute(word_str)
conn.execute(attempt_str)
conn.commit()

conn.close()

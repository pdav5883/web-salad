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
game_attr = model.Game.get_annotations()
player_attr = model.Player.get_annotations()
word_attr = model.Word.get_annotations()
attempt_attr = model.Attempt.get_annotations()


def map_col_type(col_type):
    if col_type == str:
        return "TEXT"
    elif col_type == int:
        return "INTEGER"
    elif col_type == bool:
        return "INTEGER"
    else:
        return "TEXT"


# start building table creation strings
game_str = f"CREATE TABLE {model.Game.table}("
player_str = f"CREATE TABLE {model.Player.table}("
word_str = f"CREATE TABLE {model.Word.table}("
attempt_str = f"CREATE TABLE {model.Attempt.table}("

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
game_str += "PRIMARY KEY(id))"

player_str += "PRIMARY KEY(id), " \
              "FOREIGN KEY(gid) REFERENCES game(id))"

word_str += "PRIMARY KEY(id), " \
            "FOREIGN KEY(pid) REFERENCES player(id), " \
            "FOREIGN KEY(gid) REFERENCES game(id))"

attempt_str += "PRIMARY KEY(id), " \
               "FOREIGN KEY(wid) REFERENCES word(id), " \
               "FOREIGN KEY(pid) REFERENCES player(id), " \
               "FOREIGN KEY(gid) REFERENCES game(id))"

# repopulate tables
conn.execute(game_str)
conn.execute(player_str)
conn.execute(word_str)
conn.execute(attempt_str)
conn.commit()

conn.close()

# reads characters from GOOD database into sqlite

import json
import sqlite3

characters = {}


def load(db):

    for char in db["characters"]:
        if char["key"].startswith("Traveler"):
            char["key"] = "Traveler"

        characters[char["key"]] = char

    for weapon in db["weapons"]:
        if weapon["location"]:
            characters[weapon["location"]]["weapon"] = weapon

    for artifact in db["artifacts"]:
        if artifact["location"]:
            characters[artifact["location"]][artifact["slotKey"]] = artifact


def create_table():
    with sqlite3.connect("configs.db") as con:
        cursor = con.cursor()

        cursor.execute(
            """
                CREATE TABLE IF NOT EXISTS Characters (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    level INTEGER NOT NULL,
                    ascension INTEGER NOT NULL,
                    talent TEXT NOT NULL,
                    constellation INTEGER NOT NULL,
                    weapon INTEGER NOT NULL REFERENCES Weapons(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
                    flower INTEGER REFERENCES Artifacts(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
                    plume INTEGER REFERENCES Artifacts(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
                    sands INTEGER REFERENCES Artifacts(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
                    goblet INTEGER REFERENCES Artifacts(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
                    circlet INTEGER REFERENCES Artifacts(id) ON UPDATE RESTRICT ON DELETE RESTRICT
                );
            """
        )

        cursor.execute(
            """
                CREATE TABLE IF NOT EXISTS Weapons (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    refinement INTEGER NOT NULL,
                    level INTEGER NOT NULL,
                    ascension INTEGER NOT NULL
                );
            """
        )

        cursor.execute(
            """
                CREATE TABLE IF NOT EXISTS Artifacts(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    setKey TEXT NOT NULL,
                    rarity INTEGER NOT NULL,
                    level INTEGER NOT NULL,
                    slotKey TEXT NOT NULL,
                    mainStat TEXT NOT NULL,
                    substats TEXT NOT NULL
                );
            """
        )

        cursor.execute(
            """
                CREATE TABLE IF NOT EXISTS Character_Configs(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    config_name TEXT UNIQUE NOT NULL,
                    character TEXT NOT NULL,
                    constellation INTEGER NOT NULL,
                    level TEXT NOT NULL,
                    talent TEXT NOT NULL,
                    weapon TEXT NOT NULL,
                    refine INTEGER NOT NULL,
                    config TEXT NOT NULL
                );
            """
        )

        cursor.execute(
            """
                CREATE TABLE IF NOT EXISTS Rotation_Configs(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    config_name TEXT UNIQUE NOT NULL,
                    config TEXT NOT NULL
                );
            """
        )

        cursor.execute(
            """
                CREATE TABLE IF NOT EXISTS Full_Configs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    config_name TEXT UNIQUE NOT NULL,
                    character1 TEXT REFERENCES Character_Configs(config_name) ON UPDATE RESTRICT ON DELETE RESTRICT,
                    character2 TEXT REFERENCES Character_Configs(config_name) ON UPDATE RESTRICT ON DELETE RESTRICT,
                    character3 TEXT REFERENCES Character_Configs(config_name) ON UPDATE RESTRICT ON DELETE RESTRICT,
                    character4 TEXT REFERENCES Character_Configs(config_name) ON UPDATE RESTRICT ON DELETE RESTRICT,
                    rotation TEXT REFERENCES Rotation_Configs(config_name) ON UPDATE RESTRICT ON DELETE RESTRICT
                );
            """
        )

        con.commit()


def reset_temp_tables(con, cursor):
    for table in ["Characters", "Weapons", "Artifacts"]:
        cursor.execute(f"DROP TABLE IF EXISTS {table}")
    con.commit()
    create_table()


def export():

    with sqlite3.connect("configs.db") as con:
        cursor = con.cursor()
        reset_temp_tables(con, cursor)

        for character in characters.values():
            weap = character["weapon"]
            ids = {}
            ids["key"] = character["key"]

            row = cursor.execute(
                """
                INSERT INTO weapons (name, refinement, level, ascension)
                VALUES (?,?,?,?)
                RETURNING id
                """,
                (weap["key"], weap["refinement"], weap["level"], weap["ascension"]),
            )
            ids["weapon"] = row.fetchone()[0]

            for x in ["plume", "flower", "goblet", "sands", "circlet"]:
                if x not in character:
                    continue
                artifact = (
                    character[x]["setKey"],
                    character[x]["rarity"],
                    character[x]["level"],
                    character[x]["slotKey"],
                    character[x]["mainStatKey"],
                    f'{ json.dumps({"substats": character[x]['substats']}) }',
                )
                row = cursor.execute(
                    """
                    INSERT INTO artifacts (setKey, rarity, level, slotKey, mainStat, substats)
                    VALUES (?,?,?,?,?,?)
                    RETURNING id
                    """,
                    artifact,
                )
                ids[x] = row.fetchone()[0]

            cursor.execute(
                """
                    INSERT INTO Characters (name, level, ascension, talent, constellation, weapon, flower, plume, sands, goblet, circlet)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?)
                    """,
                (
                    character["id"],
                    character["level"],
                    character["ascension"],
                    f"{character['talent']['auto']},{character['talent']['skill']},{character['talent']['burst']}",
                    character["constellation"],
                    ids["weapon"],
                    ids.get("flower"),
                    ids.get("plume"),
                    ids.get("sands"),
                    ids.get("goblet"),
                    ids.get("circlet"),
                ),
            )
            con.commit()

# uses sqlite database to create gcsim config files, ready to be used with optimisation
output_file = "sim_config.txt"

import util
import sqlite3
import json


def charToConfig(char):
    config = ""
    config += f"{char['name']} char lvl={char['lvl']} cons={char['cons']} talent={char['talent']};\n"
    config += f"{char['name']} add weapon=\"{char['weapon']['weapon']}\" refine={char['weapon']['refine']} lvl={char['weapon']['lvl']};\n"

    for k, v in char["sets"].items():
        config += f"{char['name']} add set=\"{k}\" count={v};\n"

    config += f"{char['name']} add stats"
    for k, v in char["mainStats"].items():
        config += f" {k}={v}"
    config += ";\n"

    config += f"{char['name']} add stats"
    for k, v in char["substats"].items():
        config += f" {k}={v}"
    config += ";\n"

    return config


def makeCharConfig(c):
    with sqlite3.connect("configs.db") as con:
        con.row_factory = util.dict_factory

        cursor = con.cursor()

        row = cursor.execute(
            """
            SELECT *
            FROM Characters
            WHERE Characters.name = ?
            """,
            (c,),
        ).fetchone()

        char = {
            "name": util.GOODKeytoGCSIMKey(row["name"]),
            "lvl": f"{row['level']}/{util.AscensionToMaxLevel(row['ascension'])}",
            "cons": row["constellation"],
            "talent": row["talent"],
        }

        weap = cursor.execute(
            """
            SELECT *
            FROM Weapons
            WHERE id = ?
            """,
            (row["weapon"],),
        ).fetchone()

        char["weapon"] = {
            "weapon": util.GOODKeytoGCSIMKey(weap["name"]),
            "refine": weap["refinement"],
            "lvl": f"{weap['level']}/{util.AscensionToMaxLevel(weap['ascension'])}",
        }

        mainStats = {}
        substats = {}
        sets_temp = {}
        sets = {}

        artifacts = cursor.execute(
            """
            SELECT *
            FROM Artifacts
            WHERE id IN (?, ?, ?, ?, ?)
            """,
            (
                row["flower"],
                row["plume"],
                row["sands"],
                row["goblet"],
                row["circlet"],
            ),
        ).fetchall()

        for artifact in artifacts:

            # count sets
            if artifact["setKey"] not in sets_temp.keys():
                sets_temp[artifact["setKey"]] = 1
            else:
                sets_temp[artifact["setKey"]] += 1

            for set in sets_temp.keys():
                if sets_temp[set] >= 2 and sets_temp[set] < 4:
                    sets[util.GOODKeytoGCSIMKey(set)] = 2
                elif sets_temp[set] >= 4:
                    sets[util.GOODKeytoGCSIMKey(set)] = 4

            if util.GOODStatToSimStat(artifact["mainStat"]) not in mainStats.keys():
                mainStats[util.GOODStatToSimStat(artifact["mainStat"])] = (
                    util.artifact_stats[str(artifact["rarity"])][artifact["mainStat"]][
                        artifact["level"]
                    ]
                )
            else:
                mainStats[
                    util.GOODStatToSimStat(artifact["mainStat"])
                ] += util.artifact_stats[str(artifact["rarity"])][artifact["mainStat"]][
                    artifact["level"]
                ]

            for substat in json.loads(artifact["substats"])["substats"]:
                divider = 1
                if substat["key"].endswith("_"):
                    divider = 100

                if util.GOODStatToSimStat(substat["key"]) not in substats.keys():
                    substats[util.GOODStatToSimStat(substat["key"])] = (
                        substat["value"] / divider
                    )
                else:
                    substats[util.GOODStatToSimStat(substat["key"])] += (
                        substat["value"] / divider
                    )

        char["mainStats"] = mainStats
        char["substats"] = substats
        char["sets"] = sets

        con.commit()

        return {
            "config": charToConfig(char),
            "character": row["name"],
            "constellation": char["cons"],
            "level": char["lvl"],
            "talent": char["talent"],
            "weapon": weap["name"],
            "refine": weap["refinement"],
        }


def makeTeamConfig(team):
    config = "\n".join([makeCharConfig(c)["config"] for c in team])
    return config


def writeConfig(outfile, team):
    with open(outfile, "w") as f:
        f.write(makeTeamConfig(team)["config"])


def saveConfig(c, name):
    with sqlite3.connect("configs.db") as con:
        cursor = con.cursor()

        details = makeCharConfig(c)

        cursor.execute(
            """
            INSERT INTO Character_Configs (config_name, character, constellation, level, talent, weapon, refine, config)
            VALUES (?,?,?,?,?,?,?,?)
            """,
            (
                name,
                details["character"],
                details["constellation"],
                details["level"],
                details["talent"],
                details["weapon"],
                details["refine"],
                details["config"],
            ),
        )


team = ["HuTao", "Furina", "Yelan", "Xilonen"]
[saveConfig(c, c + " v1") for c in team]

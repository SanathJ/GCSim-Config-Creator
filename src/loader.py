# reads characters from GOOD database into sqlite

import json
import sqlite3

characters = {}

to_load = ['HuTao', 'Yelan', 'Furina', 'Clorinde', 'Xilonen']

def load():
    db = {}
    with open('export.json', "r") as f:
        db = json.load(f)

    for char in db['characters']:
        if char['key'].startswith('Traveler'):
            char['key'] = 'Traveler'

        characters[char['key']] = char

    for weapon in db['weapons']:
        if weapon['location']:
            characters[weapon['location']]['weapon'] = weapon

    for artifact in db['artifacts']:
        if artifact['location']:
            characters[artifact['location']][artifact['slotKey']] = artifact

def export():
    with sqlite3.connect('configs.db') as con:
        cursor = con.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Characters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                level INTEGER NOT NULL,
                ascension INTEGER NOT NULL,
                talent TEXT NOT NULL,
                constellation INTEGER NOT NULL,
                weapon INTEGER NOT NULL REFERENCES Weapons(id) ON UPDATE RESTRICT,
                flower INTEGER NOT NULL REFERENCES Artifacts(id) ON UPDATE RESTRICT,
                plume INTEGER NOT NULL REFERENCES Artifacts(id) ON UPDATE RESTRICT,
                sands INTEGER NOT NULL REFERENCES Artifacts(id) ON UPDATE RESTRICT,
                goblet INTEGER NOT NULL REFERENCES Artifacts(id) ON UPDATE RESTRICT,
                circlet INTEGER NOT NULL REFERENCES Artifacts(id) ON UPDATE RESTRICT
            );
        ''')
    
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Weapons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                refinement INTEGER NOT NULL,
                level INTEGER NOT NULL,
                ascension INTEGER NOT NULL
            );
        ''')
    
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Artifacts(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                setKey TEXT NOT NULL,
                rarity INTEGER NOT NULL,
                level INTEGER NOT NULL,
                slotKey TEXT NOT NULL,
                mainStat TEXT NOT NULL,
                substats TEXT NOT NULL
            );
        ''')
        con.commit()

        for char in to_load:
            character = characters[char]
            weap = character['weapon']
            ids = {}
            ids['key'] = character['key']

            row = cursor.execute('''
            INSERT INTO weapons (name, refinement, level, ascension)
            VALUES (?,?,?,?)
            RETURNING id
            ''',
            (weap['key'], weap['refinement'], weap['level'], weap['ascension']))
            ids['weapon'] = row.fetchone()[0]

            
            for x in ['plume', 'flower', 'goblet', 'sands', 'circlet']:
                artifact = (character[x]['setKey'], character[x]['rarity'], character[x]['level'], character[x]['slotKey'], character[x]['mainStatKey'], f'{ json.dumps({"substats": character[x]['substats']}) }')
                row = cursor.execute('''
                INSERT INTO artifacts (setKey, rarity, level, slotKey, mainStat, substats)
                VALUES (?,?,?,?,?,?)
                RETURNING id
                ''',
                artifact)
                ids[x] = row.fetchone()[0]
            
            cursor.execute('''
                INSERT INTO characters (name, level, ascension, talent, constellation, weapon, flower, plume, sands, goblet, circlet)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)
                ''',
                (character['key'], character['level'], character['ascension'], f"{character['talent']['auto']},{character['talent']['skill']},{character['talent']['burst']}",
                 character['constellation'], ids['weapon'], ids['flower'], ids['plume'], ids['sands'], ids['goblet'], ids['circlet']))
            con.commit()
        

load()
export()

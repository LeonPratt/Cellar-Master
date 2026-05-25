import sqlite3
import os
import dotenv
dotenv.load_dotenv()

DB_DIR = os.environ.get("DB_DIR")

"""
checklist:
when adding a wine for the first time all tables are set correctly
when adding a preexisting wine only cellar.quantity changes

Can return a list of food pairings when given wineid
can return a list of wineids when given food paring <-- cellar.quantity >= 1

"""



def connect(db=DB_DIR):
    conn = sqlite3.connect(db)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def get_or_create_grape(conn, name):
    cur = conn.cursor()

    cur.execute("SELECT grapeid FROM grapes WHERE name = ?", (name,))
    row = cur.fetchone()

    if row:
        return row[0]

    cur.execute("INSERT INTO grapes (name) VALUES (?)", (name,))
    return cur.lastrowid


def get_or_create_pairing(conn, name):
    cur = conn.cursor()

    cur.execute("SELECT pairingid FROM food_pairings WHERE name = ?", (name,))
    row = cur.fetchone()

    if row:
        return row[0]

    cur.execute("INSERT INTO food_pairings (name) VALUES (?)", (name,))
    return cur.lastrowid


def wine_exists(conn, name, year):
    cur = conn.cursor()
    cur.execute(
        "SELECT wineid FROM wines WHERE name = ? AND year = ?",
        (name, year)
    )
    row = cur.fetchone()
    return row[0] if row else None

def remove_wine_from_cellar(conn, wineid:int):
    cur = conn.cursor()
    cur.execute(
        "UPDATE CELLAR SET quantity = quantity - 1 WHERE wineid = ?;",
        (wineid,))
    cur.execute(
        "DELETE FROM CELLAR WHERE wineid = ? AND quantity = 0;",
        (str(wineid),))
    conn.commit()

def get_qty_in_cellar(conn,wineid:int):
    cur = conn.cursor()
    cur.execute(
        """
        SELECT quantity FROM CELLAR WHERE wineid = ?;
        """,(wineid,)
    )
    qty = cur.fetchone()
    return qty[0]

def insert_wine(conn, data: dict):
    """
    Expected dict format:
    {
        name: str,
        year: int,
        grape_variety: list[str],
        region: str,
        tasting_notes: list[str],
        food_pairings: list[str],
        drink_window_start: int,
        drink_window_end: int,
        wine_notes: list[str]
    }
    """

    cur = conn.cursor()
    is_new_wine = False

    existing_id = wine_exists(conn, data["name"], data["year"])

    if existing_id:
        wineid = existing_id

        cur.execute("""
            UPDATE CELLAR
            SET quantity = quantity + 1
            WHERE wineid = ?;
        """, (wineid,))
    else:
        is_new_wine = True
        tasting_notes_text = " | ".join(data.get("tasting_notes", []))

        cur.execute("""
            INSERT INTO wines (name, year, region, tasting_notes)
            VALUES (?, ?, ?, ?)
        """, (
            data["name"],
            data["year"],
            data["region"],
            tasting_notes_text
        ))

        wineid = cur.lastrowid

        cur.execute("""
            INSERT INTO CELLAR (wineid, quantity)
            VALUES (?, 1)
        """, (wineid,))


    cur.execute("""
        INSERT OR REPLACE INTO drinking_windows
        (wineid, start_year, end_year)
        VALUES (?, ?, ?)
    """, (
        wineid,
        data["drink_window_start"],
        data["drink_window_end"]
    ))

    for grape in data.get("grape_variety", []):
        grape_id = get_or_create_grape(conn, grape)

        cur.execute("""
            INSERT OR IGNORE INTO wine_grapes (wineid, grapeid)
            VALUES (?, ?)
        """, (wineid, grape_id))

    for pairing in data.get("food_pairings", []):
        pairing_id = get_or_create_pairing(conn, pairing)

        cur.execute("""
            INSERT OR IGNORE INTO wine_pairings (wineid, pairingid)
            VALUES (?, ?)
        """, (wineid, pairing_id))
    if is_new_wine:
        for note in data.get("wine_notes", []):
            cur.execute("""
                INSERT INTO wine_notes (wineid, note)
                VALUES (?, ?)
            """, (wineid, note))

    conn.commit()
    return wineid

def get_all_pairings_from_wine(conn, wineid:int):
    cur = conn.cursor()
    cur.execute("SELECT pairingid FROM wine_pairings WHERE wineid = ?", (wineid))
    pairingIDs = cur.fetchall()

    pairings = []
    for pairingID in pairingIDs:
        id = pairingID[0]
        cur.execute("SELECT name FROM food_pairings WHERE pairingid = ?", (str(id)))
        pairing = cur.fetchone()
        pairings.append(pairing[0])

    return pairings

def get_all_wineids_from_pairing(conn, pairing):
    cur = conn.cursor()
    cur.execute("SELECT pairingid FROM food_pairings WHERE name = ?;", (pairing,))
    pairingid = cur.fetchone()
    if pairingid == None:
        return []
    cur.execute("SELECT wineid FROM WINE_PAIRINGS WHERE pairingid = ?;",(str(pairingid[0]),))
    wineids = cur.fetchall()
    return [x[0] for x in wineids]

if __name__ == "__main__":
    conn = connect()

    wine_data = {
        "name": "Campo viejo",
        "year": 2025,
        "grape_variety": ["rioja"],
        "region": "Rioja Alta",
        "tasting_notes": ["vanilla", "oak", "coconut"],
        "food_pairings": ["pizza", "something"],
        "drink_window_start": 2026,
        "drink_window_end": 2027,
        "wine_notes": [
            "very good value",
            "lots of oak incorporation"
        ]
    }

    #wine_id = insert_wine(conn, wine_data)
    remove_wine_from_cellar(conn,2)
    conn.close()

    #print("Inserted/updated wine ID:", wine_id)

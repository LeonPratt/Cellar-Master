import sqlite3
import os
from pathlib import Path

import dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
dotenv.load_dotenv(ROOT_DIR / ".env")

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

def remove_wine_from_cellar(conn, wineid:int, quantity:int):
    cur = conn.cursor()
    cur.execute(
        "UPDATE CELLAR SET quantity = quantity - ? WHERE wineid = ?;",
        (quantity, wineid))
    cur.execute(
        "DELETE FROM CELLAR WHERE wineid = ? AND quantity <= 0;",
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
    if qty:
        return qty[0]
    else:
        return 0

def insert_preexisting_wine(conn,wineid:int, qty:int):

    cur_qty = get_qty_in_cellar(conn, wineid)
    cur = conn.cursor()
    if cur_qty == 0:
        cur.execute(
            """
            INSERT INTO CELLAR (wineid, quantity) VALUES (?,?)
            """,(wineid, qty)
        )
        conn.commit()
    else:
        cur.execute(
            """
            UPDATE CELLAR SET quantity = quantity + ? WHERE wineid = ?;
        """,(qty, wineid)
        )
        conn.commit()
    return True

def insert_new_wine(conn, data: dict):
    """
    Expected dict format:
    {
        name: str,
        year: int,
        grape_variety: list[str],
        region: str,
        tasting_notes: str,
        food_pairings: list[str],
        drink_window_start: int,
        drink_window_end: int,
        wine_notes: list[str].
        quantity: int
    }
    """

    cur = conn.cursor()

    cur.execute("""
        INSERT INTO wines (name, year, region, tasting_notes)
        VALUES (?, ?, ?, ?)
    """, (
        data["name"],
        data["year"],
        data["region"],
        data["tasting_notes"]
    ))

    wineid = cur.lastrowid

    cur.execute("""
        INSERT INTO CELLAR (wineid, quantity)
        VALUES (?, ?)
    """, (wineid,data["quantity"]))


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

    for note in data.get("wine_notes", []):
        cur.execute("""
            INSERT INTO wine_notes (wineid, note)
            VALUES (?, ?)
        """, (wineid, note))

    conn.commit()
    return wineid

def get_all_pairings_from_wineid(conn, wineid:int):
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


def search_wines(conn, search_term="", limit=10):
    """
    Search wines by name, region, or grape name.

    Returns:
        [
            {
                "wineid": int,
                "name": str,
                "year": int,
                "region": str,
                "grapes": [str, str, ...]
            },
            ...
        ]
    """

    cursor = conn.cursor()

    if search_term.strip() == "":
        query = """
        SELECT
            w.wineid,
            w.name,
            w.year,
            w.region,
            GROUP_CONCAT(g.name) AS grapes
        FROM WINES w
        LEFT JOIN WINE_GRAPES wg ON w.wineid = wg.wineid
        LEFT JOIN GRAPES g ON wg.grapeid = g.grapeid
        GROUP BY w.wineid
        ORDER BY w.wineid
        LIMIT ?
        """

        cursor.execute(query, (limit,))

    else:
        search = f"%{search_term}%"

        query = """
        SELECT
            w.wineid,
            w.name,
            w.year,
            w.region,
            GROUP_CONCAT(DISTINCT g.name) AS grapes
        FROM WINES w
        LEFT JOIN WINE_GRAPES wg ON w.wineid = wg.wineid
        LEFT JOIN GRAPES g ON wg.grapeid = g.grapeid
        WHERE
            w.name LIKE ?
            OR w.region LIKE ?
            OR g.name LIKE ?
        GROUP BY w.wineid
        ORDER BY w.wineid
        LIMIT ?
        """

        cursor.execute(query, (search, search, search, limit))

    rows = cursor.fetchall()

    wines = []

    for row in rows:
        wines.append({
            "wineid": row[0],
            "name": row[1],
            "year": row[2],
            "region": row[3],
            "grapes": row[4].split(",") if row[4] else []
        })

    return wines


if __name__ == "__main__":
    conn = connect()

    wine_data = {
        "name": "The Virgilius",
        "year": 2001,
        "grape_variety": ["Viognier"],
        "region": "Eden Valley",
        "tasting_notes": "peach stone|floral lavender|honey butter|oak vanilla",
        "food_pairings": ["grilled chicken","roasted fish","smoked salmon","sea bass"],
        "drink_window_start": 2003,
        "drink_window_end": 2008,
        "wine_notes": [
            "very creamy",
            "lackluster on the nose"
        ],
        "quantity":3
    }

    wine_id = insert_new_wine(conn, wine_data)
    
    #remove_wine_from_cellar(conn,2)
    conn.close()

    #print("Inserted/updated wine ID:", wine_id)

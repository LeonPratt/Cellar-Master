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


def remove_wine_from_cellar(conn, wineid:int, quantity:int = -1):
    cur = conn.cursor()
    if quantity == -1:
        cur.execute(
            "DELETE FROM CELLAR WHERE wineid = ?;",
            (str(wineid),))
    cur.execute(
        "UPDATE CELLAR SET quantity = quantity - ? WHERE wineid = ?;",
        (quantity, wineid))
    cur.execute(
        "DELETE FROM CELLAR WHERE wineid = ? AND quantity <= 0;",
        (str(wineid),))
    conn.commit()

    return True

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
        wine_notes: list[str],
        quantity: int,
        imgpath:str
    }
    """

    cur = conn.cursor()

    cur.execute("""
        INSERT INTO wines (name, year, region, tasting_notes, image_path)
        VALUES (?, ?, ?, ?, ?)
    """, (
        data["name"],
        data["year"],
        data["region"],
        data["tasting_notes"],
        data["imgpath"]
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

    grape_variety = data.get("grape_variety", [])
    grape_variety = grape_variety.split(",")
    if isinstance(grape_variety, str):
        grape_variety = [grape_variety]

    for grape in grape_variety:
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
    cur.execute("SELECT pairingid FROM wine_pairings WHERE wineid = ?", (wineid,))
    pairingIDs = cur.fetchall()

    pairings = []
    for pairingID in pairingIDs:
        id = pairingID[0]
        cur.execute("SELECT name FROM food_pairings WHERE pairingid = ?", (id,))
        pairing = cur.fetchone()
        pairings.append(pairing[0])

    return pairings


def wine_id_exists(conn, wineid: int):
    cur = conn.cursor()
    cur.execute("SELECT wineid FROM wines WHERE wineid = ?", (wineid,))
    return cur.fetchone() is not None


def add_pairing_to_wine(conn, wineid: int, pairing: str):
    if not wine_id_exists(conn, wineid):
        return None

    cleaned_pairing = str(pairing or "").strip()
    if not cleaned_pairing:
        return get_all_pairings_from_wineid(conn, wineid)

    cur = conn.cursor()
    pairing_id = get_or_create_pairing(conn, cleaned_pairing)
    cur.execute("""
        INSERT OR IGNORE INTO wine_pairings (wineid, pairingid)
        VALUES (?, ?)
    """, (wineid, pairing_id))
    conn.commit()
    return get_all_pairings_from_wineid(conn, wineid)


def remove_pairing_from_wine(conn, wineid: int, pairing: str):
    if not wine_id_exists(conn, wineid):
        return None

    cleaned_pairing = str(pairing or "").strip()
    cur = conn.cursor()
    cur.execute("SELECT pairingid FROM food_pairings WHERE LOWER(name) = LOWER(?)", (cleaned_pairing,))
    row = cur.fetchone()

    if row:
        cur.execute("""
            DELETE FROM wine_pairings
            WHERE wineid = ? AND pairingid = ?
        """, (wineid, row[0]))
        conn.commit()

    return get_all_pairings_from_wineid(conn, wineid)

def get_all_wineids_from_pairing(conn, pairing):
    cur = conn.cursor()
    cur.execute("SELECT pairingid FROM food_pairings WHERE name = ?;", (pairing,))
    pairingid = cur.fetchone()
    if pairingid == None:
        return []
    cur.execute("""
        SELECT wp.wineid
            "grape_variety": ["Viognier"],
        INNER JOIN CELLAR c ON wp.wineid = c.wineid
        WHERE wp.pairingid = ? AND c.quantity > 0;
    """, (pairingid[0],))
    wineids = cur.fetchall()
    return [x[0] for x in wineids]

def update_general_data(conn, wineid: int, name: str, region: str, grapes: list, year: int, quantity: int, drink_start: int, drink_end: int):
    if not wine_id_exists(conn, wineid):
        return None

    cur = conn.cursor()

    # Update the wines table
    cur.execute("""
        UPDATE wines
        SET name = ?, region = ?, year = ?
        WHERE wineid = ?;
    """, (name, region, year, wineid))

    # Update the cellar table
    cur.execute("""
        UPDATE CELLAR
        SET quantity = ?
        WHERE wineid = ?;
    """, (quantity, wineid))

    # Update the drinking_windows table
    cur.execute("""
        UPDATE drinking_windows
        SET start_year = ?, end_year = ?
        WHERE wineid = ?;
    """, (drink_start, drink_end, wineid))
    # Update the grapes associated with the wine
    
    cur.execute("DELETE FROM wine_grapes WHERE wineid = ?", (wineid,))
    
    for grape in grapes:
        with open("debug_log.txt", "a") as f:
            f.write(f"Adding grape '{grape}' to wineid {wineid}\n")
        grape_id = get_or_create_grape(conn, grape)
        cur.execute("""
            INSERT OR IGNORE INTO wine_grapes (wineid, grapeid)
            VALUES (?, ?);
        """, (wineid, grape_id))
    
    conn.commit()

    return True


def search_wines_by_pairing(conn, pairing, limit=20):
    """
    Search cellar wines by food pairing name.

    Returns wines that have at least one bottle in the cellar and whose
    saved food pairing contains the provided search term.
    """

    search_term = pairing.strip()
    if search_term == "":
        return []

    cursor = conn.cursor()
    search = f"%{search_term}%"

    query = """
    SELECT
        w.wineid,
        w.name,
        w.year,
        w.region,
        c.quantity,
        GROUP_CONCAT(DISTINCT g.name) AS grapes,
        GROUP_CONCAT(DISTINCT fp.name) AS matched_pairings
    FROM WINES w
    INNER JOIN CELLAR c ON w.wineid = c.wineid
    INNER JOIN WINE_PAIRINGS wp ON w.wineid = wp.wineid
    INNER JOIN FOOD_PAIRINGS fp ON wp.pairingid = fp.pairingid
    LEFT JOIN WINE_GRAPES wg ON w.wineid = wg.wineid
    LEFT JOIN GRAPES g ON wg.grapeid = g.grapeid
    WHERE
        c.quantity > 0
        AND fp.name LIKE ?
    GROUP BY w.wineid
    ORDER BY w.name
    LIMIT ?
    """

    cursor.execute(query, (search, limit))
    rows = cursor.fetchall()

    wines = []
    for row in rows:
        wines.append({
            "wineid": row[0],
            "name": row[1],
            "year": row[2],
            "region": row[3],
            "quantity": row[4],
            "grapes": row[5].split(",") if row[5] else [],
            "matched_pairings": row[6].split(",") if row[6] else []
        })

    return wines


def search_wines(conn, search_term="", limit=10,in_cellar_only=1):
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
            c.quantity,
            GROUP_CONCAT(DISTINCT g.name) AS grapes
        FROM WINES w
        INNER JOIN CELLAR c ON w.wineid = c.wineid
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
            c.quantity,
            GROUP_CONCAT(DISTINCT g.name) AS grapes
        FROM WINES w
        INNER JOIN CELLAR c ON w.wineid = c.wineid
        LEFT JOIN WINE_GRAPES wg ON w.wineid = wg.wineid
        LEFT JOIN GRAPES g ON wg.grapeid = g.grapeid
        WHERE
            c.quantity > 0
            AND (
                w.name LIKE ?
                OR w.region LIKE ?
                OR g.name LIKE ?
            )
        GROUP BY w.wineid
        ORDER BY w.wineid
        LIMIT ?
        """

        cursor.execute(query, ( search, search, search, limit))

    rows = cursor.fetchall()

    wines = []

    for row in rows:
        wines.append({
            "wineid": row[0],
            "name": row[1],
            "year": row[2],
            "region": row[3],
            "quantity": row[4] or 0,
            "grapes": row[5].split(",") if row[5] else []
        })

    return wines


def get_wine_by_id(conn, wineid: int):
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            w.wineid,
            w.name,
            w.year,
            w.region,
            w.tasting_notes,
            c.quantity,
            GROUP_CONCAT(DISTINCT g.name) AS grapes,
            GROUP_CONCAT(DISTINCT fp.name) AS pairings,
            w.image_path,
            dw.start_year,
            dw.end_year,
            w.Custom_notes
        FROM WINES w
        LEFT JOIN CELLAR c ON w.wineid = c.wineid
        LEFT JOIN WINE_GRAPES wg ON w.wineid = wg.wineid
        LEFT JOIN GRAPES g ON wg.grapeid = g.grapeid
        LEFT JOIN WINE_PAIRINGS wp ON w.wineid = wp.wineid
        LEFT JOIN FOOD_PAIRINGS fp ON wp.pairingid = fp.pairingid
        LEFT JOIN drinking_windows dw ON w.wineid = dw.wineid
        WHERE w.wineid = ?
        GROUP BY w.wineid
        """,
        (wineid,)
    )

    row = cursor.fetchone()

    if not row:
        return None

    return {
        "wineid": row[0],
        "name": row[1],
        "year": row[2],
        "region": row[3],
        "tasting_notes": row[4],
        "quantity": row[5] or 0,
        "grapes": row[6].split(",") if row[6] else [],
        "pairings": row[7].split(",") if row[7] else [],
        "imgpath": f"{row[8]}.png" if row[8] else "assets/images/bottle_placeholder.png",
        "drink_window_start": row[9] if row[9] else "Unknown",
        "drink_window_end": row[10] if row[10] else "Unknown",
        "custom_notes": row[11] if row[11] else ""
    }


def get_tasting_notes(conn, wineid: int):
    cursor = conn.cursor()
    cursor.execute("SELECT tasting_notes FROM wines WHERE wineid = ?", (wineid,))
    row = cursor.fetchone()

    if not row:
        return None

    return [
        note.strip()
        for note in str(row[0] or "").split("|")
        if note.strip()
    ]


def update_tasting_notes(conn, wineid: int, notes):
    cursor = conn.cursor()
    cursor.execute("SELECT wineid FROM wines WHERE wineid = ?", (wineid,))

    if not cursor.fetchone():
        return None

    cleaned_notes = []
    for note in notes:
        cleaned = str(note or "").replace("|", " ").strip()
        if cleaned and cleaned not in cleaned_notes:
            cleaned_notes.append(cleaned)

    cursor.execute(
        "UPDATE wines SET tasting_notes = ? WHERE wineid = ?",
        ("|".join(cleaned_notes), wineid)
    )
    conn.commit()
    return cleaned_notes


def update_custom_notes(conn, wineid: int, notes):
    cursor = conn.cursor()
    cursor.execute("SELECT wineid FROM wines WHERE wineid = ?", (wineid,))

    if not cursor.fetchone():
        return None

    cursor.execute(
        "UPDATE wines SET Custom_notes = ? WHERE wineid = ?",
        (notes, wineid)
    )
    conn.commit()
    return notes

def add_tasting_note(conn, wineid: int, note: str):
    existing_notes = get_tasting_notes(conn, wineid)

    if existing_notes is None:
        return None

    return update_tasting_notes(conn, wineid, [*existing_notes, note])


def remove_tasting_note(conn, wineid: int, note: str):
    existing_notes = get_tasting_notes(conn, wineid)

    if existing_notes is None:
        return None

    note_to_remove = str(note or "").strip().lower()
    remaining_notes = [
        existing_note
        for existing_note in existing_notes
        if existing_note.lower() != note_to_remove
    ]

    return update_tasting_notes(conn, wineid, remaining_notes)


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

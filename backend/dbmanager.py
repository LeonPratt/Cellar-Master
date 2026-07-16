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

def _quote_identifier(identifier: str) -> str:
    """Quote a SQLite identifier after it has been resolved from the cellars table."""
    return '"' + identifier.replace('"', '""') + '"'


def get_cellar(conn, cellarname: str):
    """Return the canonical stored cellar name, or None when it does not exist."""
    if not isinstance(cellarname, str) or not cellarname.strip():
        return None

    row = conn.execute(
        "SELECT name FROM cellars WHERE name = ? COLLATE NOCASE",
        (cellarname.strip(),),
    ).fetchone()
    return row[0] if row else None


def _cellar_table(conn, cellarname: str):
    canonical_name = get_cellar(conn, cellarname)
    if canonical_name is None:
        return None
    return _quote_identifier(canonical_name)


def Create_Cellar(conn, name):
    name = str(name or "").strip()
    if not name or "\x00" in name:
        return None

    try:
        cur = conn.cursor()
        if get_cellar(conn, name) is not None:
            return None

        cur.execute("INSERT INTO cellars (name) VALUES(?)", (name,))
        cellarid = cur.lastrowid
        cur.execute(f"""
        CREATE TABLE {_quote_identifier(name)} (
            wineid INTEGER PRIMARY KEY,
            quantity INTEGER NOT NULL,
            FOREIGN KEY (wineid) REFERENCES wines(wineid)
                ON DELETE CASCADE
        );
        """)
        conn.commit()
        return {"cellarid": cellarid, "name": name}
    except sqlite3.Error:
        conn.rollback()
        return None

def Delete_cellar(conn, cellarid):
    try:
        cur = conn.cursor()
        row = cur.execute(
            "SELECT name FROM cellars WHERE cellarid = ?", (int(cellarid),)
        ).fetchone()
        if row is None:
            return False

        cur.execute(f"DROP TABLE {_quote_identifier(row[0])}")
        cur.execute("DELETE FROM cellars WHERE cellarid = ?", (int(cellarid),))

        conn.commit()
        return True
    except (TypeError, ValueError, sqlite3.Error):
        conn.rollback()
        return False
def get_all_cellars(conn):
    cur = conn.cursor()

    cellars = []
    rows = cur.execute("SELECT cellarid, name FROM cellars ORDER BY name COLLATE NOCASE").fetchall()
    for cellarid, name in rows:
        
        num_bottles = cur.execute(f"""
        SELECT SUM(quantity) FROM {name};
        """).fetchone()[0]
        print(cellarid,name,num_bottles)
        cellars.append({"cellarid":cellarid,"name":name,"num_bottles":num_bottles})
    return cellars
#    return [
#        {"cellarid": row[0], "name": row[1]}
#        for row in cur.execute("SELECT cellarid, name FROM cellars ORDER BY name COLLATE NOCASE")
#    ]



def get_or_create_grape(conn, name):
    cur = conn.cursor()

    cur.execute("SELECT grapeid FROM grapes WHERE name = ?", (name.title().strip(),))
    row = cur.fetchone()

    if row:
        return row[0]

    cur.execute("INSERT INTO grapes (name) VALUES (?)", (name.title().strip(),))
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


def remove_wine_from_cellar(conn, wineid: int, cellarname: str, quantity: int = -1):
    cellar_table = _cellar_table(conn, cellarname)
    if cellar_table is None:
        return False

    cur = conn.cursor()
    if quantity == -1:
        cur.execute(
            f"UPDATE {cellar_table} SET quantity = 0 WHERE wineid = ?;",
            (wineid,))
    else:
        cur.execute(
            f"UPDATE {cellar_table} SET quantity = MAX(quantity - ?, 0) WHERE wineid = ?;",
            (quantity, wineid))

    conn.commit()

    return cur.rowcount > 0

def get_qty_in_cellar(conn, wineid: int, cellarname: str):
    cellar_table = _cellar_table(conn, cellarname)
    if cellar_table is None:
        return 0

    cur = conn.cursor()
    cur.execute(
        f"""
        SELECT quantity FROM {cellar_table} WHERE wineid = ?;
        """,(wineid,)
    )
    qty = cur.fetchone()
    if qty:
        return qty[0]
    else:
        return 0

def insert_preexisting_wine(conn, wineid: int, cellarname: str, qty: int):
    cellar_table = _cellar_table(conn, cellarname)
    if cellar_table is None:
        return False

    cur_qty = get_qty_in_cellar(conn, wineid, cellarname)
    cur = conn.cursor()
    if cur_qty == 0:
        cur.execute(
            f"""
            INSERT INTO {cellar_table} (wineid, quantity) VALUES (?,?)
            """,(wineid, qty)
        )
        conn.commit()
    else:
        cur.execute(
            f"""
            UPDATE {cellar_table} SET quantity = quantity + ? WHERE wineid = ?;
        """,(qty, wineid)
        )
        conn.commit()
    return True

def insert_new_wine(conn, data: dict, cellarname: str):
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
        imgpath:str,
        price:float
    }
    """

    cellar_table = _cellar_table(conn, cellarname)
    if cellar_table is None:
        return None

    cur = conn.cursor()

    cur.execute("""
        INSERT INTO wines (name, year, region, tasting_notes, image_path, price)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        data["name"],
        data["year"],
        data["region"],
        data["tasting_notes"],
        data["imgpath"],
        data["price"]
    ))

    wineid = cur.lastrowid

    cur.execute(f"""
        INSERT INTO {cellar_table} (wineid, quantity)
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


def wine_exists_in_cellar(conn, wineid: int, cellarname: str):
    cellar_table = _cellar_table(conn, cellarname)
    if cellar_table is None:
        return False
    return conn.execute(
        f"SELECT 1 FROM {cellar_table} WHERE wineid = ?", (wineid,)
    ).fetchone() is not None


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

def get_all_wineids_from_pairing(conn, pairing, cellarname):
    cellar_table = _cellar_table(conn, cellarname)
    if cellar_table is None:
        return []

    cur = conn.cursor()
    cur.execute("SELECT pairingid FROM food_pairings WHERE name = ?;", (pairing,))
    pairingid = cur.fetchone()
    if pairingid == None:
        return []
    cur.execute(f"""
        SELECT wp.wineid
        FROM wine_pairings wp
        INNER JOIN {cellar_table} c ON wp.wineid = c.wineid
        WHERE wp.pairingid = ? AND c.quantity > 0;
    """, (pairingid[0],))
    wineids = cur.fetchall()
    return [x[0] for x in wineids]

def update_general_data(conn, wineid: int, name: str, region: str, grapes: list, year: int, quantity: int, drink_start: int, drink_end: int, price:float,cellarname: str):
    if not wine_id_exists(conn, wineid):
        return None

    cellar_table = _cellar_table(conn, cellarname)
    if cellar_table is None:
        return None

    cur = conn.cursor()

    # Update the wines table
    cur.execute("""
        UPDATE wines
        SET name = ?, region = ?, year = ?, price = ?
        WHERE wineid = ?;
    """, (name, region, year,price, wineid))

    # Update the cellar table
    cur.execute(f"""
        INSERT INTO {cellar_table} (wineid, quantity)
        VALUES (?, ?)
        ON CONFLICT(wineid) DO UPDATE SET quantity = excluded.quantity;
    """, (wineid, quantity))

    # Update the drinking_windows table
    cur.execute("""
        UPDATE drinking_windows
        SET start_year = ?, end_year = ?
        WHERE wineid = ?;
    """, (drink_start, drink_end, wineid))


    # Update the grapes associated with the wine
    
    cur.execute("DELETE FROM wine_grapes WHERE wineid = ?", (wineid,))
    
    for grape in grapes:
        grape_id = get_or_create_grape(conn, grape.title().strip())
        cur.execute("""
            INSERT OR IGNORE INTO wine_grapes (wineid, grapeid)
            VALUES (?, ?);
        """, (wineid, grape_id))
    
    conn.commit()

    return True


def search_wines_by_pairing(conn, pairing, cellarname, limit=20):
    """
    Search cellar wines by food pairing name.

    Returns wines that have at least one bottle in the cellar and whose
    saved food pairing contains the provided search term.
    """

    cellar_table = _cellar_table(conn, cellarname)
    if cellar_table is None:
        return []

    search_term = pairing.strip()
    if search_term == "":
        return []

    cursor = conn.cursor()
    search = f"%{search_term}%"

    query = f"""
    SELECT
        w.wineid,
        w.name,
        w.year,
        w.region,
        c.quantity,
        GROUP_CONCAT(DISTINCT g.name) AS grapes,
        GROUP_CONCAT(DISTINCT fp.name) AS matched_pairings
    FROM WINES w
    INNER JOIN {cellar_table} c ON w.wineid = c.wineid
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


def search_wines(conn, cellarname, search_term="", limit=10, in_cellar_only=True):
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

    cellar_table = _cellar_table(conn, cellarname)
    if cellar_table is None:
        return []

    cursor = conn.cursor()
    cellar_join = f"INNER JOIN {cellar_table} c ON w.wineid = c.wineid" if in_cellar_only else f"LEFT JOIN {cellar_table} c ON w.wineid = c.wineid"
    cellar_filter = "WHERE c.quantity > 0" if in_cellar_only else ""

    if search_term.strip() == "":
        query = f"""
        SELECT
            w.wineid,
            w.name,
            w.year,
            w.region,
            COALESCE(c.quantity, 0) AS quantity,
            GROUP_CONCAT(DISTINCT g.name) AS grapes
        FROM WINES w
        {cellar_join}
        LEFT JOIN WINE_GRAPES wg ON w.wineid = wg.wineid
        LEFT JOIN GRAPES g ON wg.grapeid = g.grapeid
        {cellar_filter}
        GROUP BY w.wineid
        ORDER BY w.wineid
        LIMIT ?
        """

        cursor.execute(query, (limit,))

    else:
        search = f"%{search_term}%"

        query = f"""
        SELECT
            w.wineid,
            w.name,
            w.year,
            w.region,
            COALESCE(c.quantity, 0) AS quantity,
            GROUP_CONCAT(DISTINCT g.name) AS grapes
        FROM WINES w
        {cellar_join}
        LEFT JOIN WINE_GRAPES wg ON w.wineid = wg.wineid
        LEFT JOIN GRAPES g ON wg.grapeid = g.grapeid
        WHERE
            {"c.quantity > 0 AND" if in_cellar_only else ""}
            (
                w.name LIKE ?
                OR w.region LIKE ?
                OR EXISTS (
                    SELECT 1
                    FROM WINE_GRAPES search_wg
                    INNER JOIN GRAPES search_g ON search_wg.grapeid = search_g.grapeid
                    WHERE search_wg.wineid = w.wineid
                      AND search_g.name LIKE ?
                )
                OR w.year LIKE ?
            )
        GROUP BY w.wineid
        ORDER BY w.wineid
        LIMIT ?
        """

        cursor.execute(query, (search, search, search, search, limit))

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


def get_wine_by_id(conn, wineid: int, cellarname: str):
    cellar_table = _cellar_table(conn, cellarname)
    if cellar_table is None:
        return None

    cursor = conn.cursor()

    cursor.execute(
        f"""
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
            w.Custom_notes,
            w.price
        FROM WINES w
        LEFT JOIN {cellar_table} c ON w.wineid = c.wineid
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
        "custom_notes": row[11] if row[11] else "",
        "price":row[12] if row[12] else ""
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

    cellar = Create_Cellar(conn, "Example Cellar") or {"name": "Example Cellar"}
    wine_id = insert_new_wine(conn, wine_data, cellar["name"])
    
    #remove_wine_from_cellar(conn,2)
    conn.close()

    #print("Inserted/updated wine ID:", wine_id)

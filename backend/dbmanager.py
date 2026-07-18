import sqlite3
import os
from pathlib import Path
import dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
dotenv.load_dotenv(ROOT_DIR / ".env")

DB_DIR = os.environ.get("DB_DIR")

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

def get_cellarID(conn, cellarname:str):
    row = conn.execute("SELECT cellarid FROM cellars WHERE name = ?;",(cellarname.strip(),)).fetchone()
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

        cur.execute("INSERT INTO cellars (name) VALUES(?);", (name,))
        cellarid = cur.lastrowid
        conn.commit()
        return {"cellarid": cellarid, "name": name}
    except sqlite3.Error:
        conn.rollback()
        return None

def Delete_cellar(conn, cellarid):
    try:
        cur = conn.cursor()

        cur.execute("DELETE FROM cellar WHERE cellarid = ?;",(cellarid,))
        cur.execute("DELETE FROM cellars WHERE cellarid = ?;",(cellarid,))
        conn.commit()
        return True
    except (TypeError, ValueError, sqlite3.Error):
        conn.rollback()
        return False
def get_all_cellars(conn):
    cur = conn.cursor()

    cellars = []
    rows = cur.execute("SELECT cellarid, name FROM cellars").fetchall()
    for cellarid, name in rows:
        
        num_bottles = cur.execute("SELECT SUM(quantity) FROM cellar WHERE cellarid = ?",(cellarid,)).fetchone()[0]
        if num_bottles is None:
            num_bottles = 0

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


def wine_exists(conn, name, year, producer):
    cur = conn.cursor()
    cur.execute(
        "SELECT wineid FROM wines WHERE name = ? AND year = ? AND producer = ?",
        (name, year, producer)
    )
    row = cur.fetchone()
    return row[0] if row else None


def remove_wine_from_cellar(conn, wineid: int, cellarname: str, quantity: int = -1):
    cellarid = get_cellarID(conn,cellarname)
    if cellarid is None:
        return 0
    cur = conn.cursor()
    if quantity == -1:
        cur.execute(
            f"UPDATE cellar SET quantity = 0 WHERE wineid = ? AND cellarid = ?;",
            (wineid,cellarid))
    else:
        cur.execute(
            f"UPDATE cellar SET quantity = MAX(quantity - ?, 0) WHERE wineid = ? AND cellarid = ?;",
            (quantity, wineid,cellarid))

    conn.commit()

    return cur.rowcount > 0

def get_qty_in_cellar(conn, wineid: int, cellarname: str):
    cellarid = get_cellarID(conn,cellarname)
    if cellarid is None:
        return 0
    cur = conn.cursor()
    cur.execute(
        f"""
        SELECT quantity FROM cellar WHERE wineid = ? AND cellarid = ?;
        """,(wineid,cellarid)
    )
    qty = cur.fetchone()
    if qty:
        return qty[0]
    else:
        return 0

def insert_preexisting_wine(conn, wineid: int, cellarname: str, qty: int):
    cellarid = get_cellarID(conn, cellarname)
    if cellarid is None:
        return False

    cur_qty = get_qty_in_cellar(conn, wineid, cellarname)
    cur = conn.cursor()
    if cur_qty == 0:
        cur.execute(
            f"""
            INSERT INTO cellar (cellarid, wineid, quantity) VALUES (?,?,?)
            """,(cellarid, wineid, qty)
        )
        conn.commit()
    else:
        cur.execute(
            f"""
            UPDATE cellar SET quantity = quantity + ? WHERE wineid = ? AND cellarid = ?;
        """,(qty, wineid, cellarid)
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
        price:float,
        producer:str
    }
    """


    cellarid = get_cellarID(conn, cellarname)
    if cellarid is None:
        return False
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO wines (name, year, region, tasting_notes, image_path, price,producer)
        VALUES (?, ?, ?, ?, ?, ?,?);
    """, (
        data["name"],
        data["year"],
        data["region"],
        data["tasting_notes"],
        data["imgpath"],
        data["price"],
        data["producer"]
    ))

    wineid = cur.lastrowid
    conn.commit()
    cur.execute(f"""
        INSERT INTO cellar (cellarid, wineid, quantity)
        VALUES (?, ?, ?)
    """, (cellarid, wineid,data["quantity"]))


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
    
    cellarid = get_cellarID(conn,cellarid)
    if cellarid is None:
        return False

    return conn.execute(
        f"SELECT 1 FROM cellar WHERE wineid = ? AND cellarid = ?", (wineid,cellarid)
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
    cellarid = get_cellarID(conn,cellarname)
    if cellarid is None:
        return []

    cur = conn.cursor()
    cur.execute("SELECT pairingid FROM food_pairings WHERE name = ?;", (pairing,))
    pairingid = cur.fetchone()
    if pairingid == None:
        return []
    cur.execute(f"""
        SELECT wp.wineid
        FROM wine_pairings wp
        INNER JOIN cellar c ON wp.wineid = c.wineid AND c.cellarid = ?
        WHERE wp.pairingid = ? AND c.quantity > 0;
    """, (cellarid, pairingid[0],))
    wineids = cur.fetchall()
    return [x[0] for x in wineids]

def update_general_data(conn, wineid: int, name: str, region: str, grapes: list, year: int, quantity: int, drink_start: int, drink_end: int, price:float,producer:str,cellarname: str):
    if not wine_id_exists(conn, wineid):
        return None

    cellarid = get_cellarID(conn,cellarname)
    if cellarid is None:
        return None

    cur = conn.cursor()
    print("prod:", producer)
    # Update the wines table
    cur.execute("""
        UPDATE wines
        SET name = ?, region = ?, year = ?, price = ?, producer = ?
        WHERE wineid = ?;
    """, (name, region, year,price, producer,wineid))
    print("here")
    # Update the cellar table
    cur.execute(f"""
        INSERT INTO cellar (cellarid, wineid, quantity)
        VALUES (?, ?, ?)
        ON CONFLICT(cellarid, wineid) DO UPDATE SET quantity = excluded.quantity;
    """, (cellarid, wineid, quantity))

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

def get_all_known_wines(conn):
    """
    returns all known wines
    Returns:
        [
            {   
                "producer":str,
                "name": str,
                "year": int,
                "region": str,
                "grapes": [str, str, ...]
            },
            ...
        ]
    """
    cursor = conn.cursor()
    query = f"""
    SELECT
        w.name,
        w.producer,
        w.year,
        w.region,
        GROUP_CONCAT(DISTINCT g.name) AS grapes
    FROM WINES w
    LEFT JOIN WINE_GRAPES wg ON w.wineid = wg.wineid
    LEFT JOIN GRAPES g ON wg.grapeid = g.grapeid
    GROUP BY w.wineid
    ORDER BY w.wineid

    """
    cursor.execute(query, ())
    rows = cursor.fetchall()
    wines = []

    for row in rows:
        wines.append({
            "name": row[0],
            "producer":row[1],
            "year": row[2],
            "region": row[3],
            "grapes": row[4]
        })

    return wines

def search_wines_by_pairing(conn, pairing, cellarname, limit=20):
    """
    Search cellar wines by food pairing name.

    Returns wines that have at least one bottle in the cellar and whose
    saved food pairing contains the provided search term.
    """

    cellar_table = _cellar_table(conn, cellarname)
    if cellar_table is None:
        return []

    cellarid = get_cellarID(conn,cellarname)
    if cellarid is None:
        return []

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
    INNER JOIN cellar c 
        ON w.wineid = c.wineid
    INNER JOIN WINE_PAIRINGS wp 
        ON w.wineid = wp.wineid
    INNER JOIN FOOD_PAIRINGS fp 
        ON wp.pairingid = fp.pairingid
    LEFT JOIN WINE_GRAPES wg 
        ON w.wineid = wg.wineid
    LEFT JOIN GRAPES g 
        ON wg.grapeid = g.grapeid
    WHERE
        c.cellarid = ?
        AND c.quantity > 0
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

    cellarid = get_cellarID(conn, cellarname)
    if cellarid is None:
        return []

    cursor = conn.cursor()

    # Decide whether wines must exist in this cellar
    if in_cellar_only:
        cellar_join = """
        INNER JOIN cellar c 
            ON w.wineid = c.wineid 
            AND c.cellarid = ?
        """
    else:
        cellar_join = """
        LEFT JOIN cellar c 
            ON w.wineid = c.wineid 
            AND c.cellarid = ?
        """

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

        LEFT JOIN WINE_GRAPES wg 
            ON w.wineid = wg.wineid

        LEFT JOIN GRAPES g 
            ON wg.grapeid = g.grapeid

        WHERE
            c.quantity > 0 OR ?
            
        GROUP BY w.wineid
        ORDER BY w.wineid
        LIMIT ?
        """

        # The extra parameter allows all wines when in_cellar_only=False
        cursor.execute(
            query,
            (
                cellarid,
                0 if in_cellar_only else 1,
                limit
            )
        )

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

        LEFT JOIN WINE_GRAPES wg 
            ON w.wineid = wg.wineid

        LEFT JOIN GRAPES g 
            ON wg.grapeid = g.grapeid

        WHERE
            (
                w.name LIKE ?
                OR w.region LIKE ?
                OR EXISTS (
                    SELECT 1
                    FROM WINE_GRAPES search_wg
                    INNER JOIN GRAPES search_g 
                        ON search_wg.grapeid = search_g.grapeid
                    WHERE search_wg.wineid = w.wineid
                    AND search_g.name LIKE ?
                )
                OR w.year LIKE ?
            )

            AND (c.quantity > 0 OR ?)

        GROUP BY w.wineid
        ORDER BY w.wineid
        LIMIT ?
        """

        cursor.execute(
            query,
            (
                cellarid,
                search,
                search,
                search,
                search,
                0 if in_cellar_only else 1,
                limit
            )
        )

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
    cellarid = get_cellarID(conn,cellarname)
    if cellarid is None:
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
            w.price,
            w.producer
        FROM WINES w
        LEFT JOIN cellar c ON w.wineid = c.wineid AND c.cellarid = ?
        LEFT JOIN WINE_GRAPES wg ON w.wineid = wg.wineid
        LEFT JOIN GRAPES g ON wg.grapeid = g.grapeid
        LEFT JOIN WINE_PAIRINGS wp ON w.wineid = wp.wineid
        LEFT JOIN FOOD_PAIRINGS fp ON wp.pairingid = fp.pairingid
        LEFT JOIN drinking_windows dw ON w.wineid = dw.wineid
        WHERE w.wineid = ?
        GROUP BY w.wineid
        """,
        (cellarid, wineid,)
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
        "price":row[12] if row[12] else "",
        "producer":row[13]
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


import sqlite3
import os
import dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
dotenv.load_dotenv(ROOT_DIR / ".env")
DB_DIR = os.environ.get("DB_DIR")
print(DB_DIR)

def create_connection(db_name=DB_DIR):
    print(f"Connecting to database: {db_name}")
    conn = sqlite3.connect(db_name)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def create_tables(conn):
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS wines (
        wineid INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        year INTEGER,
        region TEXT,
        tasting_notes TEXT,
        Custom_notes TEXT,
        image_path TEXT
    );
    """)

    # -----------------------
    # CELLAR (INVENTORY)
    # -----------------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cellar (
        wineid INTEGER PRIMARY KEY,
        quantity INTEGER NOT NULL,
        FOREIGN KEY (wineid) REFERENCES wines(wineid)
            ON DELETE CASCADE
    );
    """)

    # -----------------------
    # DRINKING WINDOW
    # -----------------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS drinking_windows (
        wineid INTEGER PRIMARY KEY,
        start_year INTEGER,
        end_year INTEGER,
        FOREIGN KEY (wineid) REFERENCES wines(wineid)
            ON DELETE CASCADE
    );
    """)

    # -----------------------
    # NOTES (MULTIPLE PER WINE)
    # -----------------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS wine_notes (
        noteid INTEGER PRIMARY KEY AUTOINCREMENT,
        wineid INTEGER NOT NULL,
        note TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (wineid) REFERENCES wines(wineid)
            ON DELETE CASCADE
    );
    """)

    # -----------------------
    # GRAPES (LOOKUP TABLE)
    # -----------------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS grapes (
        grapeid INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    );
    """)

    # -----------------------
    # WINE ↔ GRAPES (MANY-TO-MANY)
    # -----------------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS wine_grapes (
        wineid INTEGER NOT NULL,
        grapeid INTEGER NOT NULL,
        PRIMARY KEY (wineid, grapeid),
        FOREIGN KEY (wineid) REFERENCES wines(wineid)
            ON DELETE CASCADE,
        FOREIGN KEY (grapeid) REFERENCES grapes(grapeid)
            ON DELETE CASCADE
    );
    """)

    # -----------------------
    # FOOD PAIRINGS (LOOKUP TABLE)
    # -----------------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS food_pairings (
        pairingid INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    );
    """)

    # -----------------------
    # WINE ↔ FOOD PAIRINGS
    # -----------------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS wine_pairings (
        wineid INTEGER NOT NULL,
        pairingid INTEGER NOT NULL,
        PRIMARY KEY (wineid, pairingid),
        FOREIGN KEY (wineid) REFERENCES wines(wineid)
            ON DELETE CASCADE,
        FOREIGN KEY (pairingid) REFERENCES food_pairings(pairingid)
            ON DELETE CASCADE
    );
    """)

    conn.commit()


def main():
    conn = create_connection()
    create_tables(conn)
    conn.close()
    print("Database schema created successfully.")


if __name__ == "__main__":
    main()
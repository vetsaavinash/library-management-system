
import sqlite3
import pandas as pd
import shutil
from pathlib import Path

# Project files
BASE_DIR = Path(__file__).resolve().parent
DATASET_PATH = BASE_DIR / "test-00000-of-00001.parquet"
DATABASE_PATH = BASE_DIR / "database.db"
BACKUP_PATH = BASE_DIR / "database_backup_before_import.db"

# Check required files
if not DATASET_PATH.exists():
    raise FileNotFoundError(f"Dataset not found: {DATASET_PATH}")

if not DATABASE_PATH.exists():
    raise FileNotFoundError(
        "database.db not found. Run your Flask app first."
    )

# Preserve a backup before modifying the database
if not BACKUP_PATH.exists():
    shutil.copy2(DATABASE_PATH, BACKUP_PATH)
    print("Database backup created.")

# Read dataset
df = pd.read_parquet(DATASET_PATH)

required_columns = {"title", "author", "genre"}
if not required_columns.issubset(df.columns):
    raise ValueError(
        f"Dataset must contain these columns: {required_columns}"
    )

conn = sqlite3.connect(DATABASE_PATH)
cursor = conn.cursor()

try:
    # Confirm the existing table has the expected structure
    cursor.execute("PRAGMA table_info(books)")
    columns = {row[1] for row in cursor.fetchall()}

    expected = {"title", "author", "category", "quantity"}
    if not expected.issubset(columns):
        raise ValueError(
            f"Unexpected books table structure: {columns}"
        )

    # Read existing books to avoid duplicates
    cursor.execute("SELECT title, author FROM books")
    existing_books = {
        (str(title).strip().casefold(),
         str(author).strip().casefold())
        for title, author in cursor.fetchall()
    }

    imported = 0
    skipped = 0

    for _, row in df.iterrows():
        title = str(row["title"]).strip()
        author = str(row["author"]).strip()
        genre = str(row["genre"]).strip()

        if (
            pd.isna(row["title"])
            or pd.isna(row["author"])
            or not title
            or not author
        ):
            skipped += 1
            continue

        key = (title.casefold(), author.casefold())

        if key in existing_books:
            skipped += 1
            continue

        cursor.execute(
            """
            INSERT INTO books (title, author, category, quantity)
            VALUES (?, ?, ?, ?)
            """,
            (title, author, genre, 1)
        )

        existing_books.add(key)
        imported += 1

    conn.commit()

    cursor.execute("SELECT COUNT(*) FROM books")
    total_books = cursor.fetchone()[0]

    print("\nImport completed!")
    print("Books imported:", imported)
    print("Records skipped:", skipped)
    print("Total book records in database:", total_books)

except Exception:
    conn.rollback()
    raise

finally:
    conn.close()

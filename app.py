from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3

app = Flask(__name__)
app.secret_key = "library-management-dev-key"

DATABASE = "database.db"


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database():
    conn = get_db_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            category TEXT NOT NULL,
            quantity INTEGER NOT NULL CHECK (quantity >= 0)
        )
    """)
    conn.commit()
    conn.close()


@app.route("/")
def index():
    search = request.args.get("search", "").strip()

    conn = get_db_connection()

    if search:
        books = conn.execute("""
            SELECT * FROM books
            WHERE title LIKE ? OR author LIKE ?
            ORDER BY id ASC
        """, (f"%{search}%", f"%{search}%")).fetchall()
    else:
        books = conn.execute(
            "SELECT * FROM books ORDER BY id ASC"
        ).fetchall()

    stats = conn.execute("""
        SELECT
            COUNT(*) AS total_titles,
            COALESCE(SUM(quantity), 0) AS total_copies,
            COALESCE(SUM(CASE WHEN quantity <= 2 THEN 1 ELSE 0 END), 0)
                AS low_stock
        FROM books
    """).fetchone()

    conn.close()

    return render_template(
        "index.html",
        books=books,
        search=search,
        stats=stats
    )


@app.route("/add", methods=["GET", "POST"])
def add_book():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        author = request.form.get("author", "").strip()
        category = request.form.get("category", "").strip()
        quantity_text = request.form.get("quantity", "").strip()

        if not title or not author or not category or not quantity_text:
            flash("Please fill in all fields.", "error")
            return redirect(url_for("add_book"))

        try:
            quantity = int(quantity_text)
            if quantity < 0:
                raise ValueError
        except ValueError:
            flash("Quantity must be a non-negative whole number.", "error")
            return redirect(url_for("add_book"))

        conn = get_db_connection()
        conn.execute("""
            INSERT INTO books (title, author, category, quantity)
            VALUES (?, ?, ?, ?)
        """, (title, author, category, quantity))
        conn.commit()
        conn.close()

        flash("Book added successfully!", "success")
        return redirect(url_for("index"))

    return render_template("add_book.html")


@app.route("/edit/<int:book_id>", methods=["GET", "POST"])
def edit_book(book_id):
    conn = get_db_connection()
    book = conn.execute(
        "SELECT * FROM books WHERE id = ?", (book_id,)
    ).fetchone()

    if book is None:
        conn.close()
        flash("Book not found.", "error")
        return redirect(url_for("index"))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        author = request.form.get("author", "").strip()
        category = request.form.get("category", "").strip()
        quantity_text = request.form.get("quantity", "").strip()

        if not title or not author or not category or not quantity_text:
            conn.close()
            flash("Please fill in all fields.", "error")
            return redirect(url_for("edit_book", book_id=book_id))

        try:
            quantity = int(quantity_text)
            if quantity < 0:
                raise ValueError
        except ValueError:
            conn.close()
            flash("Quantity must be a non-negative whole number.", "error")
            return redirect(url_for("edit_book", book_id=book_id))

        conn.execute("""
            UPDATE books
            SET title = ?, author = ?, category = ?, quantity = ?
            WHERE id = ?
        """, (title, author, category, quantity, book_id))
        conn.commit()
        conn.close()

        flash("Book updated successfully!", "success")
        return redirect(url_for("index"))

    conn.close()
    return render_template("edit_book.html", book=book)


@app.route("/delete/<int:book_id>", methods=["POST"])
def delete_book(book_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM books WHERE id = ?", (book_id,))
    conn.commit()
    conn.close()

    flash("Book deleted successfully.", "success")
    return redirect(url_for("index"))


if __name__ == "__main__":
    initialize_database()
    app.run(debug=True)
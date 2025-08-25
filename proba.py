from cs50 import SQL

db = SQL("sqlite:///tracker.db")

files = db.execute("SELECT file_name FROM transactions WHERE user_id = ?", 7)
print(files)

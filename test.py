from cs50 import SQL

db = SQL("sqlite:///finance.db")

#db.execute("CREATE TABLE history (user_id INTEGER NOT NULL, symbol TEXT NOT NULL, name TEXT NOT NULL, shares INTEGER NOT NULL, type TEXT NOT NULL, time DATETIME NOT NULL, FOREIGN KEY(user_id) REFERENCES users(id))")
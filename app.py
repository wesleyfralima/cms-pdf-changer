#import os

#from tempfile import mkdtemp
from cs50 import SQL
from flask import Flask, redirect, render_template, request, session
#from flask import flash
from werkzeug.security import check_password_hash, generate_password_hash
from flask_session import Session

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""

    # Get user Portfolio
    user_id = session["user_id"]
    user_portfolio = db.execute(
        "SELECT * FROM owned WHERE user_id = ?", user_id)
    cash_owned = db.execute(
        "SELECT cash FROM users WHERE id = ?", user_id)[0]["cash"]

    # Get updated stocks values and calculate total USD value
    share_value = 0
    total_owned = 0
    for item in user_portfolio:
        # Get the updated price of each symbol
        price = lookup(item["symbol"])["price"]
        # Insert price in the Portfolio
        item["price"] = price
        # Calculate how much the user total shares are worth for this symbol
        share_value = price * item["shares"]
        # Add this worth to portfolio
        item["total"] = share_value
        # Update total owned in portfolio
        total_owned = total_owned + share_value

    total_owned = total_owned + cash_owned

    # Render right template passing the Portfolio
    return render_template("index.html", user_portfolio=user_portfolio,
                           cash_owned=cash_owned, total_owned=total_owned)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""

    if request.method == "POST":
        # Get symbol information using API
        info = lookup(request.form.get("symbol"))
        # Check if info is not None, meaning it's not invalid
        if not info:
            return apology("Invalid symbol")

        # Analize if number of shares typed is an int
        try:
            shares = int(request.form.get("shares"))
        except ValueError:
            return apology("Shares must be an integer")

        # Check if number of shares is positive
        if shares <= 0:
            return apology("Invalid number of shares")

        # Get useful information
        user_id = session["user_id"]
        symbol = info["symbol"]
        name = info["name"]
        price = float(info["price"])

        # Get current amount of cash the user has
        cash = db.execute("SELECT cash FROM users WHERE id = ?", user_id)[
            0]["cash"]
        # Calculate the cost of the transaction
        cost = price * shares

        # Check if user has enough case
        if cost > cash:
            return apology("CAN'T AFFORD")

        # Get a list of symbols the user has
        symbols = db.execute(
            "SELECT symbol FROM owned WHERE user_id = ?", user_id)

        # If the typed symbol is already owned, update quantity of shares
        if {"symbol": symbol} in symbols:
            owned_shares = db.execute(
                "SELECT shares FROM owned WHERE user_id = ? AND symbol = ?",
                user_id, symbol)[0]["shares"]
            db.execute("UPDATE owned SET shares = ? WHERE user_id = ? AND symbol = ?",
                       owned_shares + shares, user_id, symbol)

        # If not, create new entry for that symbol
        else:
            db.execute("INSERT INTO owned (user_id, symbol, name, shares) VALUES (?, ?, ?, ?)",
                       user_id, symbol, name, shares)

        # Update user cash amount
        db.execute("UPDATE users SET cash = ? WHERE id = ?",
                   cash - cost, user_id)

        # Update the history inserting the transaction
        db.execute("INSERT INTO history (user_id, symbol, name, shares, type, time, price) VALUES \
                  (?, ?, ?, ?, 'buy', CURRENT_TIMESTAMP, ?)", user_id, symbol, name, shares, price)

        # Redirect to main page
        return redirect("/")

    return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""

    # Get user history
    transactions = db.execute(
        "SELECT * FROM history WHERE user_id = ?", session["user_id"])

    return render_template("history.html", transactions=transactions)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        if not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?",
                          request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()
    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""

    if request.method == "POST":
        info = lookup(request.form.get("symbol"))
        if not info:
            return apology("Invalid symbol")

        name = info["name"]
        price = info["price"]
        symbol = info["symbol"]

        return render_template("quoted.html", name=name, symbol=symbol, price=price)

    return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register new user."""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Ensure username was submitted
        if not username:
            return apology("Must provide username.", 400)

        # Ensure username has no special characters
        if not username.isalnum():
            return apology("Username can't contain special characters.")

        # Ensure password and password confirmation were submitted
        if not password or not confirmation:
            return apology("Must provide password and confirmation", 400)

        # Ensure password confirmation match
        if not password == confirmation:
            return apology("Password confirmation must match.", 400)

        # Query database for typed username
        rows = db.execute("SELECT * FROM users WHERE username = ?", username)
        rows_number = len(rows)

        # Ensure username does not exist
        if not rows_number == 0:
            return apology("This username is taken already.", 400)

        # Store username and password into the database
        db.execute("INSERT INTO users (username, hash) VALUES (?, ?)",
                   username, generate_password_hash(password))

        # Keep registered user logged in
        rows = db.execute("SELECT * FROM users WHERE username = ?",
                          request.form.get("username"))
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    # Get user list of symbols
    user_id = session["user_id"]
    symbols = db.execute("SELECT symbol FROM owned WHERE user_id = ?", user_id)

    if request.method == "POST":
        # Check correct input of shares
        try:
            shares = int(request.form.get("shares"))
        except ValueError:
            return apology("Invalid number of shares")

        # Check if number of shares is positive
        if shares <= 0:
            return apology("Invalid number of shares")

        # Check correct input of symbol
        symbol = request.form.get("symbol")
        if not symbol:
            return apology("Invalid symbol")

        # Check if user has the symbol to sell
        if {"symbol": symbol} not in symbols:
            return apology("Must have the stock to sell")

        # Check if user has the enough shares to sell
        owned_shares = db.execute(
            "SELECT shares FROM owned WHERE user_id = ? AND symbol = ?",
            user_id, symbol)[0]["shares"]

        if owned_shares < shares:
            return apology("You don't have that much of shares")

        # Check updated price of symbol
        info = lookup(request.form.get("symbol"))
        if not info:
            return apology("Can't check stock price now")

        # Update user shares/symbols owned
        if owned_shares - shares > 0:
            db.execute("UPDATE owned SET shares = ? WHERE user_id = ? AND symbol = ?",
                       owned_shares - shares, user_id, symbol)
        else:
            db.execute(
                "DELETE FROM owned WHERE user_id = ? AND symbol = ?", user_id, symbol)

        # Get current amount of cash the user has
        cash = db.execute("SELECT cash FROM users WHERE id = ?", user_id)[
            0]["cash"]
        # Calculate the earning of the transaction
        price = info["price"]
        earnings = price * shares
        # Update user cash amount
        db.execute("UPDATE users SET cash = ? WHERE id = ?",
                   cash + earnings, user_id)

        # Update the history inserting the transaction
        name = info["name"]
        db.execute("INSERT INTO history (user_id, symbol, name, shares, type, time, price) VALUES \
                  (?, ?, ?, ?, 'sell', CURRENT_TIMESTAMP, ?)",
                   user_id, symbol, name, shares * (-1), price)

        return redirect("/")

    return render_template("sell.html", symbols=symbols)

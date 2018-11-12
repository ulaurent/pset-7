import os

import datetime

from datetime import date
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
# Whenever we make a request from the server, it actually fetches from the server as apposed to the cache
# so we get fresh data everytime
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


@app.route("/")
@login_required #Meaning the user must be logged in to access the specific route
def index():
    """Show portfolio of stocks"""
    transactions = db.execute("SELECT * FROM portfolio WHERE id = :userID", userID = session["user_id"])
    totalBalance = db.execute("SELECT * FROM users WHERE id = :userID", userID = session["user_id"])
    balance = totalBalance[0]["cash"]

    totalHoldings = 0

    for row in transactions:
        totalHoldings += (row["price"] * row["shares"])

    return render_template("index.html", transaction = transactions, balance = balance, totalHoldings = totalHoldings)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":
        if not request.form.get("ticker"):
            return apology("Ticker Empty")
        elif not request.form.get("buy"):
            return apology("Please choose number of shares")
        elif (int)(request.form.get("buy")) <= 0:
            return apology("Number of stocks cannot be less than zero")

        symbol = request.form.get("ticker")
        stock = lookup(symbol)
        shares = (int)(request.form.get("buy"))

        #making sure tiker lookup worked
        if not stock:
            return apology("Invalid stock ticker")

        user = db.execute("SELECT * FROM users WHERE id = :username", username = session["user_id"])
        userBalance = float(user[0]["cash"])
        sharePrice = stock["price"] * shares
        totalBalance = (userBalance - sharePrice)

        if sharePrice > userBalance:
            return apology("Not enough money in your account")
        else:
            time = str(datetime.datetime.strptime(datetime.datetime.today().strftime("%Y-%m-%d %H:%M:%S"),"%Y-%m-%d %H:%M:%S"))
            #Add Transaction to portfolio
            db.execute("INSERT INTO portfolio (price,time,symbol,shares, id) VALUES (:price,:time,:symbol,:shares, :userID)",
                         price = stock["price"], time = time, symbol = stock["symbol"], shares = shares, userID = session["user_id"])
            #Adjust total cash amount from users per session
            db.execute("UPDATE users SET cash = :adjustedAmount WHERE id = :userID",
                        adjustedAmount = totalBalance, userID = session["user_id"])

            return redirect("/")

    elif request.method == "GET":
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    transactions = db.execute("SELECT * FROM portfolio WHERE id = :userID", userID = session["user_id"])
    totalBalance = db.execute("SELECT * FROM users WHERE id = :userID", userID = session["user_id"])
    balance = totalBalance[0]["cash"]


    return render_template("history.html", transaction = transactions)


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
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
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

        #check to see if symbol was submitted
        if not request.form.get("symbol"):
            return apology("Did not enter ticker")

        symbol = request.form.get("symbol")
        quote = lookup(symbol)

        if quote:
            return render_template("quoted.html", company=quote["name"], symbol=quote["symbol"], price = quote["price"])
        else:
            return apology("Symbol Ticker does not exist", 500)

    #Show stock requested// Else send apology invlaid stock
    else:
        return render_template("quotes.html")


@app.route("/register", methods=["GET", "POST"])
def register():

    """Register user"""
    # Forget any user_id, clears autologin which is the session
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        #Check to see if username already exist in database
        result = db.execute("SELECT username FROM users WHERE username = :username",
                            username = request.form.get("username"))
        if result:
            return apology("Username already exist, choose new one",401)

        #Ensure the username was filled
        if not request.form.get("username"):
            return apology("must provide username", 403)

        #Ensure the password was filled
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        #Ensure the confirm-password is filled
        elif not request.form.get("confirmation"):
            return apology("must confirm password", 403)

        #Ensure confirm-password is the same as the password
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("password and confirmed-password not the same", 403)

        #Insert information into DB, with password HASHED
        add = db.execute("INSERT INTO users (username, hash) VALUES (:username,:hash_pass)",
                        username = request.form.get("username"),
                        hash_pass = generate_password_hash(request.form.get("password")))

        return redirect("/login")

    elif request.method == "GET":

        return render_template("register.html")

@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method == "GET":

        ownedStocks = db.execute("SELECT symbol FROM portfolio WHERE id = :userID GROUP BY symbol", userID = session["user_id"])
        stock = []
        for symbol in ownedStocks:
            stock.append(symbol["symbol"])

        return render_template("sell.html", stocks = stock)

    elif request.method == "POST":

        if not request.form.get("symbol"):
            return apology("Must Specify Stock")

        if not request.form.get("shares"):
            return apology("Must Specifiy Quanitity")

        shares = float(request.form.get("shares"))
        symbol = request.form.get("symbol")
        search = lookup(symbol)

        # Get users cash amount
        cashBalance = (db.execute("SELECT cash FROM users WHERE id = :userID", userID = session["user_id"]))
        balance_cash = float(cashBalance[0]["cash"])
        setCash = (shares *((float)(search["price"]))) + balance_cash

        #Update users Total Holding Value


        # Update users cash amount available
        db.execute("UPDATE users SET cash = :setCash WHERE id = :userID", setCash = setCash, userID = session["user_id"])

        # Update Users Portfolio
        time = str(datetime.datetime.strptime(datetime.datetime.today().strftime("%Y-%m-%d %H:%M:%S"),"%Y-%m-%d %H:%M:%S"))
        db.execute("INSERT INTO portfolio (price,time,symbol,shares, id) VALUES (:price,:time,:symbol,:shares, :userID)",
                         price = search["price"], time = time, symbol = symbol, shares = (shares)*(-1), userID = session["user_id"])

        return render_template("sell.html")



def errorhandler(e):
    """Handle error"""
    return apology(e.name, e.code)


# listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

import os

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
    return apology("TODO")


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
        quote = lookup(symbol)
        shares = (int)(request.form.get("buy"))

        #making sure tiker lookup worked
        if quote:
            user = db.execute("SELECT * FROM users WHERE id = :username", username = session["user_id"])
            userBalance = float(user[0]["cash"])
            sharePrice = quote["price"] * shares
            totalBalance = (userBalance - sharePrice)

            if userBalance > sharePrice:
                #Add Transaction to portfolio
                db.execute("INSERT INTO transactions (id, price, symbol) VALUES (:userID,:price,:company)",
                                            userID = session["user_id"], price = quote["price"], company = quote["symbol"])
                #Adjust total cash amount from users per session
                adjustAmount = db.execute("UPDATE users SET cash = :adjustedAmount WHERE id = :userID",
                                adjustedAmount = totalBalance, userID = session["user_id"])

                return redirect("/")

            else:
                return apology("Not enough money in your account")

        else:
            return apology("Invalid stock ticker")

    elif request.method == "GET":
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    return apology("TODO")


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
    return apology("TODO")


def errorhandler(e):
    """Handle error"""
    return apology(e.name, e.code)


# listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

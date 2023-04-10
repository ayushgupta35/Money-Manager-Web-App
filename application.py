import os
from time import sleep
from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from helpers import apology, login_required, lookup, convert, usd
import pytz
import requests

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///money.db")


@app.route("/", methods=["GET", "POST"])
@login_required
def index(action=None, item_id=None):

    if request.method == "POST":

        if request.form['button'] == 'add':

            if not request.form.get("purchase"):
                flash("Must provide purchase")
                return render_template("index.html")
            if not request.form.get("amount"):
                flash("Must provide amount")
                return render_template("index.html")
            if not request.form.get("date"):
                flash("Must provide date")
                return render_template("index.html")
            if not request.form.get("catagory"):
                flash("Must provide catagory")
                return render_template("index.html")
            if float(request.form.get("amount")) <= 0:
                flash("Amount must be positive")
                return render_template("index.html")

            expenses = db.execute("SELECT * FROM expenses WHERE id = :user_id ORDER BY number DESC", user_id=session["user_id"])

            try:
                number = int(expenses[0]["number"]) + 1
            except:
                number = 1

            pst = pytz.timezone('America/Los_Angeles')

            purchase = request.form.get("purchase")
            amount = request.form.get("amount")
            date = request.form.get("date")
            time = datetime.time(datetime.now(pst))
            catagory = request.form.get("catagory")

            db.execute("INSERT INTO expenses (id, purchase, amount, date, catagory, time, number) VALUES (:id, :purchase, :amount, :date, :catagory, :time, :number)",
                id=session["user_id"], purchase=purchase, amount=amount, date=date, catagory=catagory, time=time, number=number)

            users = db.execute("SELECT * FROM users WHERE id = :user_id", user_id=session["user_id"])

            balance = users[0]["balance"]
            balance = usd(balance) - usd(amount)

            food = users[0]["food"]
            currency = users[0]["currency"]
            shopping = users[0]["shopping"]
            bills = users[0]["bills"]
            other = users[0]["other"]

            if catagory == "shopping":
                shopping = usd(shopping) + usd(amount)
            if catagory == "food":
                food = usd(food) + usd(amount)
            if catagory == "bills":
                bills = usd(bills) + usd(amount)
            if catagory == "other":
                other = usd(other) + usd(amount)

            sleep(1)

            db.execute("UPDATE users SET balance = :balance, shopping = :shopping, food = :food, bills = :bills, other = :other WHERE id = :user_id",
                                user_id=session["user_id"], shopping=shopping, food=food, bills=bills, other=other, balance=balance)

            users = db.execute("SELECT * FROM users WHERE id = :user_id", user_id=session["user_id"])

            balance = usd(users[0]["balance"])
            food = usd(users[0]["food"])
            currency = users[0]["currency"]
            shopping = usd(users[0]["shopping"])
            bills = usd(users[0]["bills"])
            other = usd(users[0]["other"])

            if balance < 0:
                flash("Warning: negative funds")
            elif balance < 50:
                flash("Warning: low funds")

            expenses = db.execute("SELECT * FROM expenses WHERE id = :user_id ORDER BY number DESC", user_id=session["user_id"])

            flash("Added new expense!")

            return render_template("index.html", balance=balance, currency=currency, shopping=shopping, food=food, other=other, bills=bills, expenses=expenses)

        if request.form['button'] == 'search':

            if not request.form.get("search"):
                flash("No search entry provided")
                return render_template("index.html")

            search = request.form.get("search")

            users = db.execute("SELECT * FROM users WHERE id = :user_id", user_id=session["user_id"])

            balance = usd(users[0]["balance"])
            food = usd(users[0]["food"])
            currency = users[0]["currency"]
            shopping = usd(users[0]["shopping"])
            bills = usd(users[0]["bills"])
            other = usd(users[0]["other"])

            if balance < 0:
                flash("Warning: negative funds")
            elif balance < 50:
                flash("Warning: low funds")

            searchtable = db.execute("SELECT * FROM expenses WHERE purchase = :search OR amount = :search OR date = :search OR time = :search OR catagory = :search OR number = :search", search=search)

            flash("Searched up entry!")
            return render_template("index.html", searchtable=searchtable, balance=balance, currency=currency, shopping=shopping, food=food, other=other, bills=bills)

        if request.form['button'] == 'reset':

            users = db.execute("SELECT * FROM users WHERE id = :user_id", user_id=session["user_id"])

            balance = usd(users[0]["balance"])
            food = usd(users[0]["food"])
            currency = users[0]["currency"]
            shopping = usd(users[0]["shopping"])
            bills = usd(users[0]["bills"])
            other = usd(users[0]["other"])

            if balance < 0:
                flash("Warning: negative funds")
            elif balance < 50:
                flash("Warning: low funds")

            expenses = db.execute("SELECT * FROM expenses WHERE id = :user_id ORDER BY number DESC", user_id=session["user_id"])

            return render_template("index.html", balance=balance, currency=currency, shopping=shopping, food=food, other=other, bills=bills, expenses=expenses)

        if request.form['button'] == 'deleterow':

            if float(request.form.get("deleterow")) <= 0:
                flash("Id must be positive")
                return render_template("index.html")

            id = int(request.form.get("deleterow"))

            users = db.execute("SELECT * FROM users WHERE id = :user_id", user_id=session["user_id"])

            expenses = db.execute("SELECT * FROM expenses WHERE number = :id", id=id)

            catagory = expenses[0]["catagory"]
            amount = expenses[0]["amount"]
            balance = usd(users[0]["balance"])
            food = usd(users[0]["food"])
            currency = users[0]["currency"]
            shopping = usd(users[0]["shopping"])
            bills = usd(users[0]["bills"])
            other = usd(users[0]["other"])

            if catagory == "funds":
                balance = usd(balance) - usd(amount)
            if catagory == "shopping":
                balance = usd(balance) + usd(amount)
                shopping = usd(shopping) - usd(amount)
            if catagory == "food":
                balance = usd(balance) + usd(amount)
                food = usd(food) - usd(amount)
            if catagory == "bills":
                balance = usd(balance) + usd(amount)
                bills = usd(bills) - usd(amount)
            if catagory == "other":
                balance = usd(balance) + usd(amount)
                other = usd(other) - usd(amount)

            db.execute("UPDATE users SET balance = :balance, shopping = :shopping, food = :food, bills = :bills, other = :other WHERE id = :user_id",
                                user_id=session["user_id"], shopping=shopping, food=food, bills=bills, other=other, balance=balance)

            sleep(1)

            db.execute("DELETE FROM expenses WHERE number = :id", id=id)

            users = db.execute("SELECT * FROM users WHERE id = :user_id", user_id=session["user_id"])

            balance = usd(users[0]["balance"])
            food = usd(users[0]["food"])
            currency = users[0]["currency"]
            shopping = usd(users[0]["shopping"])
            bills = usd(users[0]["bills"])
            other = usd(users[0]["other"])

            if balance < 0:
                flash("Warning: negative funds")
            elif balance < 50:
                flash("Warning: low funds")

            expenses = db.execute("SELECT * FROM expenses WHERE id = :user_id ORDER BY number DESC", user_id=session["user_id"])

            return render_template("index.html", balance=balance, currency=currency, shopping=shopping, food=food, other=other, bills=bills, expenses=expenses)


    else:
        users = db.execute("SELECT * FROM users WHERE id = :user_id", user_id=session["user_id"])

        balance = usd(users[0]["balance"])
        food = usd(users[0]["food"])
        currency = users[0]["currency"]
        shopping = usd(users[0]["shopping"])
        bills = usd(users[0]["bills"])
        other = usd(users[0]["other"])

        if balance < 0:
            flash("Warning: negative funds")
        elif balance < 50:
            flash("Warning: low funds")

        expenses = db.execute("SELECT * FROM expenses WHERE id = :user_id ORDER BY number DESC", user_id=session["user_id"])

        return render_template("index.html", balance=balance, currency=currency, shopping=shopping, food=food, other=other, bills=bills, expenses=expenses)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            flash("Must provide username")
            return render_template("login.html")

        # Ensure password was submitted
        elif not request.form.get("password"):
            flash("Must provide password")
            return render_template("login.html")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            flash("Invalid username and/or password")
            return render_template("login.html")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        flash("Logged In!")

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
    flash("Logged Out!")
    return redirect("/login")


@app.route("/funds", methods=["GET", "POST"])
@login_required
def funds():
    """Allow user to add funds"""

    if request.method == "POST":

        if not request.form.get("amount"):
            flash("No amount specified")
            return render_template("funds.html")
        if not request.form.get("source"):
            flash("No source specified")
            return render_template("funds.html")
        if float(request.form.get("amount")) <= 0:
                flash("Amount must be positive")
                return render_template("funds.html")

        users = db.execute("SELECT * FROM users WHERE id = :user_id", user_id=session["user_id"])

        amount = request.form.get("amount")
        balance = users[0]["balance"]

        balance = usd(balance) + usd(amount)

        db.execute("UPDATE users SET balance = :balance WHERE id = :user_id", user_id=session["user_id"], balance=balance)

        sleep(1)

        expenses = db.execute("SELECT * FROM expenses WHERE id = :user_id ORDER BY number DESC", user_id=session["user_id"])

        pst = pytz.timezone('America/Los_Angeles')

        try:
            number = int(expenses[0]["number"]) + 1
        except:
            number = 1

        purchase = request.form.get("source")
        amount = request.form.get("amount")
        date = datetime.date(datetime.now(pst))
        time = datetime.time(datetime.now(pst))
        catagory = "funds"

        db.execute("INSERT INTO expenses (id, purchase, amount, date, catagory, time, number) VALUES (:id, :purchase, :amount, :date, :catagory, :time, :number)",
            id=session["user_id"], purchase=purchase, amount=amount, date=date, catagory=catagory, time=time, number=number)

        flash("Added Funds!")
        return redirect("/")

    else:
        return render_template("funds.html")



@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    """Allow user to change settings"""

    if request.method == "POST":

        if request.form['button'] == 'password':

            if not request.form.get("oldpassword"):
                flash("Must provide current password")
                return render_template("change.html")

            rows = db.execute("SELECT hash FROM users WHERE id = :user_id", user_id=session["user_id"])

            if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("oldpassword")):
                flash("Invalid password")
                return render_template("change.html")

            if not request.form.get("newpassword"):
                flash("Must provide new password")
                return render_template("change.html")

            elif not request.form.get("newpasswordconfirmation"):
                flash("Must provide new password confirmation")
                return render_template("change.html")

            elif request.form.get("newpassword") != request.form.get("newpasswordconfirmation"):
                flash("Passwords do not match")
                return render_template("change.html")

            hash = generate_password_hash(request.form.get("newpassword"))
            rows = db.execute("UPDATE users SET hash = :hash WHERE id = :user_id", user_id=session["user_id"], hash=hash)

            flash("Changed password!")

            return redirect("/")

        elif request.form['button'] == 'currency':

            if not request.form.get("currency"):
                flash("No currency selected")
                return render_template("change.html")

            users = db.execute("SELECT * FROM users WHERE id= :user_id", user_id=session["user_id"])

            expenses = db.execute("SELECT * FROM expenses WHERE id= :user_id", user_id=session["user_id"])

            balance = users[0]["balance"]
            shopping = users[0]["shopping"]
            food = users[0]["food"]
            bills = users[0]["bills"]
            other = users[0]["other"]
            currency = request.form.get("currency").upper()
            oldcurrency = users[0]["currency"].upper()

            balance = convert(oldcurrency, currency, balance)
            shopping = convert(oldcurrency, currency, shopping)
            food = convert(oldcurrency, currency, food)
            bills = convert(oldcurrency, currency, bills)
            other = convert(oldcurrency, currency, other)

            for i in range(len(expenses)):
                amount = expenses[i]["amount"]
                amount = usd(convert(oldcurrency, currency, amount))
                time = expenses[i]["time"]
                date = expenses[i]["date"]
                db.execute("UPDATE expenses SET amount = :amount WHERE time= :time AND date= :date", amount=amount, time=time, date=date)

            db.execute("UPDATE users SET currency = :currency, balance = :balance, shopping = :shopping, food = :food, bills = :bills, other = :other WHERE id = :user_id",
                            user_id=session["user_id"], currency=currency, balance=balance, shopping=shopping, food=food, bills=bills, other=other)

            flash("Changed currency!")
            return redirect("/")

        elif request.form['button'] == 'delete':

            if not request.form.get("delete"):
                flash("Checkbox not confirmed")
                return render_template("change.html")

            db.execute("DELETE FROM users WHERE id = :user_id", user_id = session["user_id"])

            sleep(1)

            db.execute("DELETE FROM expenses WHERE id = :user_id", user_id = session["user_id"])

            session.clear()
            flash("Deleted Account")
            return redirect("/login")


        else:
            flash("Unable to change. Try again!")
            return redirect("/")

    else:
        return render_template("change.html")




@app.route("/forgot", methods=["GET", "POST"])
def forgot():
    '''Allow user to reset password'''

    if request.method == "POST":

        if not request.form.get("username"):
            flash("Must provide username")
            return render_template("register.html")

        elif not request.form.get("password"):
            flash("Must provide password")
            return render_template("register.html")

        elif not request.form.get("confirmation"):
            flash("Must provide password confirmation")
            return render_template("register.html")

        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        if password == confirmation:
            db.execute("UPDATE users SET hash = :hash WHERE username = :username", hash=generate_password_hash(request.form.get("password")), username=request.form.get("username"))

        else:
            flash("Passwords do not match")
            return render_template("register.html")

        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            flash("Invalid username and/or password")
            return render_template("register.html")

        session["user_id"] = rows[0]["id"]

        flash("Reset!")

        return redirect("/")

    else:
        return render_template("forgot.html")




@app.route("/register", methods=["GET", "POST"])
def register():
    '''Allow user to register'''

    if request.method == "POST":

        if not request.form.get("username"):
            flash("Must provide username")
            return render_template("register.html")

        elif not request.form.get("password"):
            flash("Must provide password")
            return render_template("register.html")

        elif not request.form.get("confirmation"):
            flash("Must provide password confirmation")
            return render_template("register.html")

        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        if password == confirmation:
            db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)",
                    username=request.form.get("username"), hash=generate_password_hash(request.form.get("password")))

        else:
            flash("Passwords do not match")
            return render_template("register.html")

        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            flash("Invalid username and/or password")
            return render_template("register.html")

        session["user_id"] = rows[0]["id"]

        flash("Registered!")

        return redirect("/")

    else:
        return render_template("register.html")



def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

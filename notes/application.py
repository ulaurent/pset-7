from flask import Flask, render_template
from cs50 import SQL


app = Flask(__name__)


db = SQL("sqlite:///customer.db") #access database

rows = db.execute("SELECT * FROM customer")

for row in rows:
    print(f"{row['name']} registered")

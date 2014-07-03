from flask import Flask
from raven.flask_glue import AuthDecorator
import psycopg2, psycopg2.extras

app = Flask(__name__)
app.secret_key = "JQJsuNp609YMlhQAA_paScAumIHgzMp_fZWlainGBmjx8NFIx0"
auth_dec = AuthDecorator(desc="Engineering module sharing")

app.before_request(auth_dec.before_request)

with psycopg2.connect("dbname=engmodules user=joe") as conn:
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute('SELECT * FROM modules')
    modules = cur.fetchall()

from app import views

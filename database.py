from flask import Flask, jsonify
import os
import psycopg2
from dotenv import load_dotenv
import seed as SEED

load_dotenv()

app = Flask(__name__)
db_url=os.getenv("DATABASE_URL")
host = "rosie.db.elephantsql.com"
databae = "uibtguct"
user = "uibtguct"
password = "qCbrrW0C4yVjdE9cJEpgq-j-Y1hu3Tx7"

connection = psycopg2.connect(host=host, database=databae, user=user, password=password)


@app.get('/seed/org')
def create_org():
    with connection:
            with connection.cursor() as cursor:
                user = cursor.execute("SELECT * FROM users LIMIT 1")
                return (user)


if __name__ == '__main__':
    app.run(debug=True)
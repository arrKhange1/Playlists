from flask_sqlalchemy import SQLAlchemy

import pymysql
from db_config import host, user, password, db_name

from flask import Flask, render_template, request

try:
    connection = pymysql.connect(
        host = host,
        user = user,
        password= password,
        database=db_name,
        cursorclass=pymysql.cursors.DictCursor
    )
    print("Successfully connected...")


except Exception as ex:
    print("Connection failed...")
    print(ex)



app = Flask(__name__)


@app.route("/", methods=['GET','POST'])
def index():
    print(request.form)
    return render_template("index.html")

@app.route("/playlists_page")
def playlists():
    return render_template("playlists.html")


if __name__ == "__main__":
    app.run(debug=True)

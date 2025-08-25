from flask import Flask, redirect, render_template, request, session
from flask_session import Session
from cs50 import SQL
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import login_required
from pdf_functions import sign_file, download_file
from datetime import datetime
import os, random


app = Flask(__name__)

# configure session
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# configure database
db = SQL("sqlite:///tracker.db")

# configuer upload folder for files
UPPLOAD_FOLDER = "documents"
app.config["UPPLOAD_FOLDER"] = UPPLOAD_FOLDER


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/dashboard")
@login_required
def dashboard():
    transactions = db.execute("SELECT * FROM transactions WHERE user_id = ?", session["user_id"])
    return render_template("dashboard.html", transactions=transactions)


@app.route("/sign", methods=["GET", "POST"])
@login_required
def sign():
    if request.method == "POST":
        # get document type and indexing
        doc_type = request.form.get("doctype")
        signature_name = request.form.get("signature")
        rows = db.execute("SELECT * FROM signatures WHERE name = ?", signature_name)
        signature_link = rows[0]["link"]

        if doc_type == "barauslagen":
            image_x = 120
            image_y = 590

        # get uploaded data
        document = request.files["file_upload"]
        if document.filename != "":
            # document upload, save file to the foder on the server
            file_id = random.randint(100000, 999999)
            file_name = f"{file_id}.pdf"
            file_path = os.path.join(app.config["UPPLOAD_FOLDER"], file_name)
            document.save(file_path)

            # call the signature function
            result_url = sign_file(file_path, signature_link, image_x, image_y)

            # call the download function
            download_file(result_url, file_name)
            # log the process in transactions table
            date = str(datetime.now())
            transaction_date = date.partition(".")
            transaction_date = transaction_date[0]

            db.execute("INSERT INTO transactions (file_name, date, user_id) VALUES(?,?,?)", file_name, transaction_date, session["user_id"])

            return render_template("upload_ok.html", filename=file_name)

        else:
            return render_template("upload_error.html")

    else:
        return render_template("sign.html")


@app.route("/download", methods=["GET", "POST"])
@login_required
def settings():
    # if the users selects a document to download
    if request.method == "POST":
        filename = request.form.get("document")

        return render_template("upload_ok.html", filename=filename)

    else:
        files = db.execute("SELECT file_name FROM transactions WHERE user_id = ?", session["user_id"])
        return render_template("download.html", files=files)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # basic error checking
        if not request.form.get("username"):
            return render_template("register_error_user.html")
        elif not request.form.get("email"):
            return render_template("register_error_email.html")
        elif not request.form.get("password") or not request.form.get("confirmation"):
            return render_template("register_error_pass.html")
        elif request.form.get("password") != request.form.get("confirmation"):
            return render_template("register_error_pass.html")
        else:
            user_name = request.form.get("username")
            user_email = request.form.get("email")
            hash_password = generate_password_hash(request.form.get("password"))

            try:
                db.execute("INSERT INTO users (username, pass_hash, email) VALUES (?,?,?)", user_name, hash_password, user_email)
            except ValueError:
                return render_template("register_error_data.html")

            return render_template("reg_ok.html")

    else:
        # in case of GET request
        return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    session.clear()

    if request.method == "POST":
        # error checking
        if not request.form.get("username"):
            return render_template("register_error_user.html")
        elif not request.form.get("password"):
            return render_template("register_error_pass.html")

        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        if len(rows) != 1 or not check_password_hash(rows[0]["pass_hash"], request.form.get("password")):
            return render_template("login_error.html")

        session["user_id"] = rows[0]["id"]

        return redirect("/dashboard")

    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# Todo
# implement documents sql table: id - primary key // filename - text // date - text -> create a variable in python and place it in

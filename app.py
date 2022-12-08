import os

#from tempfile import mkdtemp
from cs50 import SQL
from flask import Flask, redirect, render_template, request, session, send_file, after_this_request
from flask import flash
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from PyPDF2 import PdfFileReader
from flask_session import Session
from shutil import rmtree

from helpers import apology, login_required


# Define list of available functions and their "route"
FUNCTIONS = [
    {"href": "/extract", "title": "Extract Text"},
    {"href": "/delete", "title": "Delete Pages"},
    {"href": "/include", "title": "Include Pages"},
    {"href": "/divide", "title": "Divide Pages"},
    {"href": "/merge", "title": "Merge Files"},
    {"href": "/split", "title": "Split Files"},
    {"href": "/ocr", "title": "Detect Text"}
]
UPLOAD_FOLDER = 'static/uploads/'
ALLOWED_EXTENSIONS = ['pdf']

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///pdf.db")


@app.context_processor
def inject_functions():
    """ Make variable visible to all templates, without passing it"""
    return dict(FUNCTIONS=FUNCTIONS)


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


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
        # if not username.isalnum():
        #    return apology("Username can't contain special characters.")

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


@app.route("/")
@login_required
def index():
    """Display available functions"""

    return apology("TODO")


def allowed_file(filename):
    """ Check if file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/download')
def download_file(output_file_path):
    """ Downloads a file"""
    file_handle = open(output_file_path, mode='r', encoding='UTF-8')
    @after_this_request
    def remove_file(output_file_path):
        try:
            os.system('rmdir /S /Q "{}"'.format(output_file_path))
            file_handle.close()
        except Exception as error:
            raise Exception("Error removing or closing downloaded file handle", error) from error
        return redirect("/extract")
    return send_file(output_file_path)


@app.route("/extract", methods=["GET", "POST"])
@login_required
def extract():
    """Change PDF pages order"""

    if request.method == 'POST':
        # Get user id
        user_id = "user_" + str(session["user_id"]) + "/"

        # check if the post request has the file part
        if 'file' not in request.files:
            return redirect(request.url)

        file = request.files['file']

        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            return redirect(request.url)

        if file and allowed_file(file.filename):
            os.mkdir(UPLOAD_FOLDER + user_id)

            filename = secure_filename(file.filename)
            uploaded_file = UPLOAD_FOLDER + user_id + filename

            #uploaded_file = os.path.join(UPLOAD_FOLDER, filename)

            flash(uploaded_file)
            file.save(uploaded_file)

        pdf_reader = PdfFileReader(uploaded_file)

        output_file_path = UPLOAD_FOLDER + user_id + filename + ".txt"

        with open(output_file_path, mode="w", encoding='UTF-8') as output_file:
            title = pdf_reader.documentInfo.title
            num_pages = pdf_reader.getNumPages()
            output_file.write(f"{title}\nNumber of pages: {num_pages}\n\n")

            for page in pdf_reader.pages:
                text = page.extractText()
                output_file.write("Next Page\n\n")
                output_file.write(text)
                output_file.write("\n\n\n")

        return download_file(UPLOAD_FOLDER + user_id)

    return render_template("extract.html")



@app.route("/delete")
@login_required
def delete():
    """Delete PDF pages"""

    return apology("TODO")


@app.route("/include", methods=["GET", "POST"])
@login_required
def include():
    """Include PDF pages"""

    return apology("TODO")


@app.route("/divide", methods=["GET", "POST"])
@login_required
def divide():
    """Cut PDF page into two pages"""

    return apology("TODO")


@app.route("/merge")
@login_required
def merge():
    """Merge two PDF files"""

    return apology("TODO")


@app.route("/split", methods=["GET", "POST"])
@login_required
def split():
    """Split PDF files"""

    return apology("TODO")


@app.route("/ocr", methods=["GET", "POST"])
@login_required
def ocr():
    """Split PDF files"""

    return apology("TODO")

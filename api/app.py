# pylint: disable=no-member

import os
import copy

from shutil import rmtree
from cs50 import SQL
from flask import Flask, redirect, render_template, request, session, send_file
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader, PdfWriter, PdfMerger
from flask_session import Session

from helpers import apology, login_required


# Define list of available functions and their "route"
FUNCTIONS = [
    {"href": "/extract", "title": "Extract Text",
    "explanation": "Use this function to extract text from a PDF file and save it to a TXT file."},

    {"href": "/delete", "title": "Delete Pages",
    "explanation": "Use this function to delete a range of pages from a PDF file."},

    {"href": "/include", "title": "Include Pages",
    "explanation": "Use this function to include some blank pages to a PDF file."},

    {"href": "/divide", "title": "Divide Pages",
    "explanation": "Use this function to crop a PDF file with two columns. Save with one column."},

    {"href": "/merge", "title": "Merge Files",
    "explanation": "Use this function to merge two PDF file into a single PDF file."},

    {"href": "/split", "title": "Extract Pages",
    "explanation": "Use this function to extract a range of pages from a PDF file."},

    #{"href": "/ocr", "title": "Detect Text",
    #"explanation": "Use this function to extract text from a PDF file and save it to a TXT file."},
]
UPLOAD_FOLDER = 'static/uploads/'
ALLOWED_EXTENSIONS = ['pdf']

# Configure application
app = Flask(__name__)
app.secret_key = os.urandom(12)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

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


@app.route("/")
@login_required
def index():
    """Display available functions"""

    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register new user."""

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


def delete_user_files():
    """ Delete files uploaded or generated by user"""
    if session["user_id"] is not None:
        user_dir = UPLOAD_FOLDER + "user_" + str(session["user_id"]) + "/"
        if os.path.isdir(user_dir):
            rmtree(user_dir)


@app.route("/logout")
def logout():
    """Log user out"""

    # Delete user files
    delete_user_files()
    # Forget any user_id
    session.clear()
    # Redirect user to login form
    return redirect("/")


def allowed_file(filename):
    """ Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def check_file(out_extension):
    """ Get user and file info, setting uder folder, and check some usage"""

    # Set file name
    file = request.files['file']
    # Set user folder
    user_dir = "user_" + str(session["user_id"]) + "/"
    # Set folder to save the out .txt file
    dir_to = UPLOAD_FOLDER + user_dir

    # Create user folder if not present
    if not os.path.isdir(dir_to):
        os.mkdir(dir_to)

    # Make sure there's no maliciuos file name
    filename = secure_filename(file.filename)
    # Full path to save uploaded .pdf
    uploaded_file = dir_to + filename
    # Save uploaded file into disk
    file.save(uploaded_file)

    # Create instance of PDF Reader
    pdf_reader = PdfReader(uploaded_file)

    # Create file for output .txt file
    output_file = dir_to + filename.replace(".pdf", "") + out_extension

    return pdf_reader, output_file


@app.route("/extract", methods=["GET", "POST"])
@login_required
def extract():
    """Extract PDF text to .txt file"""

    if request.method == 'POST':
        # Set file name
        file = request.files['file']

        # check if the user selected any file
        if not file:
            return apology("must select file")

        # check if the user select a .pdf file
        if not allowed_file(file.filename):
            return apology("this is not a .pdf file")

        pdf_reader, output_file = check_file(".txt")

        # Perform .PDF "conversion"
        with open(output_file, mode="w", encoding='UTF-8') as out:
            out.write(f"File title: {pdf_reader.documentInfo.title} \
                \nNumber of pages: {pdf_reader.getNumPages()}\n\n\n")

            for page in pdf_reader.pages:
                text = page.extractText() + "\n\n\n\n"
                out.write(text)

        # Let user download .txt file
        return send_file(output_file, as_attachment=True)

    # If page was reached via GET
    return render_template("extract.html")


@app.route("/delete", methods=["GET", "POST"])
@login_required
def delete():
    """Delete PDF pages"""

    # If user got into page via POST request
    if request.method == "POST":

        # Set file name
        file = request.files['file']

        # check if the user selected any file
        if not file:
            return apology("must select file")

        # check if the user select a .pdf file
        if not allowed_file(file.filename):
            return apology("this is not a .pdf file")

        # Check file type and return output_filename and PdfReader instance
        pdf_reader, output_file = check_file(".pdf")

        # Try to parse start and end to an integer
        try:
            start_page = int(request.form.get("start"))
            end_page = int(request.form.get("end"))
        # Render error page if not possible
        except (TypeError, ValueError):
            return apology("Start and End must be integers")

        # Get number of pages in original file
        pages_in_file = pdf_reader.getNumPages()
        # Get a range of pages to be deleted
        pages_range = range(start_page - 1, end_page)

        # Check if start and end page interval is valid for the file
        if start_page < 1 or end_page > pages_in_file:
            return apology("This page interval is invalid for this file")

        # Create new PdfWriter instance
        pdf_writer = PdfWriter()

        # Go through every page in original file
        for i in range(pages_in_file):
            # Skip pages to be deleted
            if i in pages_range:
                continue
            # If page should not be deleted, add it to new file
            page = pdf_reader.getPage(i)
            pdf_writer.addPage(page)

        # Create the new .pdf file
        pdf_writer.write(output_file)

        # Let user download the generated file
        return send_file(output_file, as_attachment=True)

    # If user got into page via GET request
    return render_template("delete.html")


@app.route("/include", methods=["GET", "POST"])
@login_required
def include():
    """Include blank PDF pages"""

    # If user got into page via POST request
    if request.method == "POST":

        # Set file name
        file = request.files['file']

        # check if the user selected any file
        if not file:
            return apology("must select file")

        # check if the user select a .pdf file
        if not allowed_file(file.filename):
            return apology("this is not a .pdf file")

        # Check file type and return output_filename and PdfReader instance
        pdf_reader, output_file = check_file(".pdf")

        # Try to parse start and end to an integer
        try:
            start_page = int(request.form.get("start"))
            end_page = int(request.form.get("end"))
        # Render error page if not possible
        except (TypeError, ValueError):
            return apology("Start and End must be integers")

        # Get number of pages in original file
        pages_in_file = pdf_reader.getNumPages()
        # Get a range of pages to be deleted
        pages_range = range(start_page - 1, end_page)

        # Check if start and end page interval is valid for the file
        if start_page < 1 or end_page > pages_in_file:
            return apology("This page interval is invalid for this file")

        # Create new PdfWriter instance
        pdf_writer = PdfWriter()

        file_dimensions = pdf_reader.pages[0].mediaBox
        #blank_page = pdf_writer.addBlankPage(file_dimensions[2], file_dimensions[3])

        # Go through every page in original file
        for i in range(pages_in_file):
            # Add normal page to new file
            page = pdf_reader.getPage(i)
            pdf_writer.addPage(page)

            # Add blank page
            if i in pages_range:
                pdf_writer.addBlankPage(file_dimensions[2], file_dimensions[3])

        # Create the new .pdf file
        pdf_writer.write(output_file)

        # Let user download the generated file
        return send_file(output_file, as_attachment=True)

    # If user got into page via GET request
    return render_template("include.html")


@app.route("/divide", methods=["GET", "POST"])
@login_required
def divide():
    """Cut PDF page into two pages"""

    # If user got into page via POST request
    if request.method == "POST":

        # Set file name
        file = request.files['file']

        # check if the user selected any file
        if not file:
            return apology("must select file")

        # check if the user select a .pdf file
        if not allowed_file(file.filename):
            return apology("this is not a .pdf file")

        # Check file type and return output_filename and PdfReader instance
        pdf_reader, output_file = check_file(".pdf")

        # Get number of pages in original file
        pages_in_file = pdf_reader.getNumPages()

        # Create new PdfWriter instance
        pdf_writer = PdfWriter()

        # Go through every page in original file
        for i in range(pages_in_file):
            # Get original page's info
            page = pdf_reader.getPage(i)
            current_coords = page.mediaBox.upperRight

            # Make two copys of page
            left_side = copy.deepcopy(page)
            right_side = copy.deepcopy(page)

            # Update coords of page
            new_coords = (current_coords[0] / 2, current_coords[1])

            # Set the two new pages
            left_side.mediaBox.upperRight = new_coords
            right_side.mediaBox.upperLeft = new_coords

            # Add both left and right portions of page
            pdf_writer.addPage(left_side)
            pdf_writer.addPage(right_side)

        # Create the new .pdf file
        pdf_writer.write(output_file)

        # Let user download the generated file
        return send_file(output_file, as_attachment=True)

    # If user got into page via GET request
    return render_template("divide.html")


@app.route("/merge", methods=["GET", "POST"])
@login_required
def merge():
    """Merge two PDF files"""

    # If user got into page via POST request
    if request.method == "POST":

        # Set files names
        first_file = request.files['first-file']
        second_file = request.files['second-file']

        # check if the user selected any file
        if not first_file or not second_file:
            return apology("must select file")

        # check if the user select a .pdf file
        if not allowed_file(first_file.filename) or not allowed_file(second_file.filename):
            return apology("this is not a .pdf file")

        # Check file type and return output_filename
        # Set user folder
        user_dir = "user_" + str(session["user_id"]) + "/"
        # Set folder to save the out .txt file
        dir_to = UPLOAD_FOLDER + user_dir
        # Create user folder if not present
        if not os.path.isdir(dir_to):
            os.mkdir(dir_to)
        # Make sure there's no maliciuos file name
        first_filename = secure_filename(first_file.filename)
        second_filename = secure_filename(second_file.filename)
        # Full path to save uploaded .pdf
        first_uploaded_file = dir_to + first_filename
        second_uploaded_file = dir_to + second_filename
        # Save uploaded file into disk
        first_file.save(first_uploaded_file)
        second_file.save(second_uploaded_file)

        # Create file for output .txt file
        output_file = dir_to + first_filename.replace(".pdf", "") + " -merged with- " + \
            second_filename.replace(".pdf", "") + ".pdf"

        # Create a list with both files
        files = [first_uploaded_file, second_uploaded_file]

        # Create new PdfWriter instance
        pdf_merger = PdfMerger()

        for file in files:
            pdf_merger.append(file)

        # Create the new .pdf file
        pdf_merger.write(output_file)

        # Let user download the generated file
        return send_file(output_file, as_attachment=True)

    # If user got into page via GET request
    return render_template("merge.html")


@app.route("/split", methods=["GET", "POST"])
@login_required
def split():
    """Split PDF files"""

    # If user got into page via POST request
    if request.method == "POST":

        # Set file name
        file = request.files['file']

        # check if the user selected any file
        if not file:
            return apology("must select file")

        # check if the user select a .pdf file
        if not allowed_file(file.filename):
            return apology("this is not a .pdf file")

        # Check file type and return output_filename and PdfReader instance
        pdf_reader, output_file = check_file(".pdf")

        # Try to parse start and end to an integer
        try:
            start_page = int(request.form.get("start"))
            end_page = int(request.form.get("end"))
        # Render error page if not possible
        except (TypeError, ValueError):
            return apology("Start and End must be integers")

        # Get number of pages in original file
        pages_in_file = pdf_reader.getNumPages()
        # Get a range of pages to be deleted
        pages_range = range(start_page - 1, end_page)

        # Check if start and end page interval is valid for the file
        if start_page < 1 or end_page > pages_in_file:
            return apology("This page interval is invalid for this file")

        # Create new PdfWriter instance
        pdf_writer = PdfWriter()

        # Go through every page in original file
        for i in range(pages_in_file):
            if i in pages_range:
                page = pdf_reader.getPage(i)
                pdf_writer.addPage(page)

        # Create the new .pdf file
        pdf_writer.write(output_file)

        # Let user download the generated file
        return send_file(output_file, as_attachment=True)

    # If user got into page via GET request
    return render_template("split.html")


@app.route("/ocr", methods=["GET", "POST"])
@login_required
def ocr():
    """Detect text in PDF files"""

    return apology("TODO")

if __name__ == '__main__':
    app.run(debug=True)
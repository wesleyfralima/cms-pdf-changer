# Couple More Studio's PDF Changer Web Application
#### Video Demo: https://youtu.be/oz6QQCe8Fng
***
***

## Important to Consider
This project is the final project for the course CS50's Introduction to Computer Science, attended in edX, 100% online, from October 3th 2022 to December 18th 2022.

***
## About
Couple More Studio's PDF Changer is a small project of a web application using Python, Flask, HTML, CSS, and Javascript. It also uses a lot of Bootstrap's classes and functions. The objective of this application is to provide some free tools relataded to PDF files modifications.
The app can be found in https://couplemore.pythonanywhere.com/ (won't be forever found there), hosted in Pythonanywhere's server.

***
## Tools (or Functions)
The PDF Changer app, as up to now, contains the following functions:
- ***Extract Text***, which allows users to automaticaly extract text from a PDF file and save it to a TXT file;
- ***Delete Pages***, which allows users to delete a range of pages from a PDF file:
- ***Include Pages***, which allows users to include a blank page after each normal page in a rage of pages in the PDF file;
- ***Divide Pages***, which allows users to cut a two-column page and save it as a two-page one-column format;
- ***Merge Files***, which allows users to combine two PDF, given the second file will be inserted right after the last page of the first file;
- ***Extract Pages***, which allows users to extract a range of pages from PDF file and save it to a new PDF file.

***
## Folders and Files
As it is required in a Flask application, the project contains:
- A file called `app.py`, containing the main logic for the application;
- A folder called `static`, cointaining static files, like CSS stylesheets, JS code files, images, and more;
- A folder called `templates`, containing an HTML file for each webpage in the application:
    - One file for each of the app's functions;
    - One file for an error page, called `apology.html`;
    - One page for the main layout;
    - One page for the index page;
    - One page for users login (login is required just for the sake of practicing what was taught at the course);
    - One page for users logout;
    - One page for users registration.
- In the `static` folder there's a subfolder called `uploads`, and its goal is to store files that users have uploaded.

Not required for Flask, but it also contains the following files:
- A file called `helpers.py`, which contains some functions used to control and/or check informations in the main file;
- A file called `pdf.db`, which is a database to store users username and hashed passwords (along with each user's unique index).

Of course there are the ordinary
- `README.md` (this file);
- `requirements.txt` (for listing the project's required Python Libraries);
- `.gitignore` folder (for telling Git not to track some files and folders).

***
## Project Status
The project is finished in the sense that it is fully functioning in what it promises. This does not mean it will never receive any more functions or updates (see bellow). Of course this also does not mean it is bug free.

***
## Intended Future Implementations
In the future, the following implementations are intended to be made:
- Any related bugs fixes;
- Addition of the OCR function, which will be able to detect text in PDF files that contains it as images;
- Additon of PDF to Office (docx, xls, ppt) conversion;
- Addition of Office to PDF conversion;
- Better visuals;
- Better UX;
- Better UI;

***
## Decisions
The application in intended to have a simple interface, simple visuals, and simple undestanding. 
The way the app is, it stores every PDF file uploaded by users. Each user has their own folder (called `user_152`, where the number is the user unique index). 
The files are deleted if the user changes the page to another page of this application (including any other function, login and logout pages, index page) or refreshes the current page. It has a problem yet because the files will not be deleted if the user closes the tab or the browser. So her/his files will be there until she/he access the web app again. 
In order to prevent the server to be full of useless files, it was created a function that deletes every files from every user. This function is called when the index page is rendered. Of course, this could cause future problems, when a user is uploading a file and other user is deleting every file in a short time intervel (very short). 
I could not find a well designed solution for this.

***
## Credits
Image credits:
- Heart/Joystick image (`static/files/logo.png`): https://logopond.com/3ab2ou/showcase/detail/295773;
- Social Media logo are from each of their website.
# Digital Signature App

#### Video Demo:  https://youtu.be/2tsrymrU0wI

#### Description:
This is a web application created with python/flask that simulates a digital signature process.
It enables users to sign pdf documents with their own digitalized signature (stored as .png file), and thereby it streamlines internal busines processes. My colleagues at work spent a lot of time signing documents for internal processes by hand. This way the document had to be printed out, signed manually, scanned back, and sent to the original recipient in an email attachment. The problem presented itself, and my solution was simple: i scanned in the signatures, created simple png files from them with transparent background, and created a web application which in essence copies these images on the pdf document at a specific index or position.

#### The tech stack used:
- html, css, bootstrap 5
- python, flask
- sqlite3
- pdf.co API, https://docs.pdf.co/

#### The application flow and structure:
1. The user selects the type of the document he wants to sign. This is needed because the indexation where the signature needs to be placed can differ from document to document.
2. The user selects the signature he wants to use. This function only exists in the current POC version (Proof of concept) to test out some basic functionality. In later versions this will be determined automatically using session_id of the user.
3. The user needs to upload the pdf file itself. The current version only accepts pdf, but doc, and docx will be also implemented in a later version.
4. The user clicks the “sign” button, and through various http requests (GET, POST, PUT) the selected signature gets placed on the document.
5. The user can view and download the signed document.

I have used python/flask to create the routes which the application uses:
- Register: without login the user can only view index.html, and every other part is restricted. The user needs to create a username, and password to register. This data is stored in a SQL table called "users". The password is hashed and stored accordingly in the database. The application checks if all data has been submitted, and displays an html page with an error message is something is missing.
- Login: the user has to login through this page by submitting his username and password. This is needed to access all other pages besides index.html, which only shares basic information regarding the application. In case the username or password is incorrect the user is redirected to an html page which displays an error message.
- Dashboard: every document which the user signed in the past using the application is displayed here in a tabular fashion. The user can see the name of the file, the date, and the file's unique id number. When the function which signs the document runs, the name of the file, and the date are being stored in the “transactions” SQL table, which also has the user_id as foreign key stored. This way the connection between users and signed documents are established. I use a for loop with Jinja syntax to display data regarding signed documents only specific to the user who is logged in (session_id).
- Sign a document: This is the part where the most important things happen. The application uses these two API endpoints from pdf.co:<br/>
https://api.pdf.co/v1/file/upload/get-presigned-url -> this is used to request a pre-signed-url and temporarily upload the pdf document.
<br/>
https://api.pdf.co/v1/pdf/edit/add -> this is used to insert the png image (signature) into the pdf file at a specific index.

I have structured all the http requests in a separate module called “pdf_functions.pdf” which needs to be imported before use. The main functions doing the work here are:
```
def sign_file(file_path, signature_link, x, y):
    # get presigned url for temporary upload with pdf.co
    headers = {
        "x-api-key": API_KEY
    }

    presigned_r = requests.get("https://api.pdf.co/v1/file/upload/get-presigned-url", headers=headers)
    presigned_r_json = presigned_r.json()
    presigned_url = presigned_r_json["presignedUrl"]
    document_url = presigned_r_json["url"]

    # upload the pdf using the presigned url
    with open(file_path, "rb") as file:
        upload_r = requests.put(presigned_url, data=file)

    # sign the document with signature of the user -> user_id
    payload = {
    "url": document_url,
    "name": "result.pdf",
    "images": [
        {
        "url": signature_link,
        "x": x,
        "y": y,
        "width": 480,
        "height": 160,
        "pages": "0"
        }
    ],
    "async": False
    }

    signature_r = requests.post("https://api.pdf.co/v1/pdf/edit/add", headers=headers, data=json.dumps(payload))
    signature_r_json = signature_r.json()
    result_url = signature_r_json["url"]
    return result_url
```

This takes the file path, the link to the signature, and the x and y positions as integers to first upload the document to a temporary storage, and place the signature image on the x and y positions. These positions are determined in app.py when the user defines which document to sign:

```
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
```
This way it's possible to store the index data according to the document

The second function within this module downloads the signed document from the pdf.co server using a GET request:
```
def download_file(result_url, filename):
    # downloads the pdf file which has been signed
    download_r = requests.get(result_url)

    if download_r.status_code == 200:
        file_path = f"static/{filename}"
        with open(file_path, "wb") as result:
            result.write(download_r.content)
    else:
        print("download failed")
```

- Download a document: this route enables the user to select a document which he has already signed and download it. Every signed document is stored under “/static” and is named as a digit integer number, which is randomly generated:
```
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
```

It is important to note that this version is mainly a “Proof of Concept” (POC) to test out the solution and some basic functionality. This is the reason the UI is really basic, which will be updated in a later version. 





# this module has the functions which call pdf.co API
import requests
import json

with open("api_key.txt", "r") as key_file:
    API_KEY = key_file.read().strip()

FILE_PATH = "docu_to_sign.pdf"


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


def download_file(result_url, filename):
    # downloads the pdf file which has been signed
    download_r = requests.get(result_url)

    if download_r.status_code == 200:
        file_path = f"static/{filename}"
        with open(file_path, "wb") as result:
            result.write(download_r.content)
    else:
        print("download failed")


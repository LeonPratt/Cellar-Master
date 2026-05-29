import os
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
from werkzeug.utils import secure_filename

from backend import infer_wine_details


import os
from dotenv import load_dotenv
load_dotenv("C:\\Users\\leona\\OneDrive\\Documents\\GitHub\\vinum\\.env")

PEM_PATH = os.environ.get("PEM_PATH")
print(PEM_PATH)
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / 'uploads'
UPLOAD_DIR.mkdir(exist_ok=True)

app = Flask(__name__)

@app.route('/')
def index():
    return send_from_directory(BASE_DIR, 'home.html')

@app.route('/home.js')
def home_js():
    return send_from_directory(BASE_DIR, 'home.js')


@app.route('/camera/verify/')
def verify():
    return send_from_directory(BASE_DIR, 'verify.html')

@app.route('/camera/verify/verify.js')
def verify_js():
    return send_from_directory(BASE_DIR, 'verify.js')

@app.route('/camera')
def camera_page():
    return send_from_directory(BASE_DIR, 'camera.html')

@app.route('/camera.js')
def camera_js():
    return send_from_directory(BASE_DIR, 'camera.js')

@app.route('/switch_cam.png')
def switch_cam():
    return send_from_directory(BASE_DIR, 'switch_cam.png')

@app.route('/HomePagebg.png')
def getHomePageBG():
    return send_from_directory(BASE_DIR, 'HomePagebg.png')

@app.route('/upload-photo', methods=['POST'])
def upload_photo():
    if 'photo' not in request.files:
        return jsonify({'message': 'No photo file provided.'}), 400

    photo = request.files['photo']
    if photo.filename == '':
        return jsonify({'message': 'No file name provided.'}), 400

    filename = secure_filename(photo.filename)
    if filename == '':
        filename = 'photo.png'

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    save_name = f'{timestamp}_{filename}'
    save_path = UPLOAD_DIR / save_name
    photo.save(save_path)

    details = infer_wine_details.infer_basic(save_path, True)
    print(details)
    return jsonify({'message': 'Photo saved successfully.', 'filename': save_name.split(".png")[0], 'name':details['name'], 'year':details['year'], 'grape_variety':details['grape_variety'], 'region':details['region']})

@app.route('/uploads/<path:filename>')
def serve_upload(filename):
    return send_from_directory(UPLOAD_DIR, filename)


@app.route('/add-to-cellar', methods=['POST'])
def add():
    data = request.get_json()
    print("added")
    try:
        infer_wine_details.Add_to_cellar(data)
        print(data)
        return jsonify({"status": "added"})
    except:
        return jsonify({"status":"failed"})


@app.route('/remove-from-cellar', methods=['POST'])
def remove():
    data = request.get_json()

    try:
        infer_wine_details.Remove_from_cellar(data)
        print(data)
        return jsonify({"status": "removed"})
    except:
        return jsonify({"status":"failed"})


if __name__ == '__main__':
    cert_path = f"{PEM_PATH}/cert.pem"
    key_path = f"{PEM_PATH}/key.pem"
    ssl_context = (str(cert_path), str(key_path))
    app.run(host='0.0.0.0', port=5000, debug=True, ssl_context=ssl_context)

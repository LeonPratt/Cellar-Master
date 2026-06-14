import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory
from werkzeug.utils import secure_filename
import dbmanager
import infer_wine_details

BACKEND_DIR = Path(__file__).resolve().parent
ROOT_DIR = BACKEND_DIR.parent
FRONTEND_DIR = ROOT_DIR / "frontend"
PAGES_DIR = FRONTEND_DIR / "pages"
SCRIPTS_DIR = FRONTEND_DIR / "scripts"
ASSETS_DIR = FRONTEND_DIR / "assets"
UPLOAD_DIR = ROOT_DIR / "uploads"

load_dotenv(ROOT_DIR / ".env")

UPLOAD_DIR.mkdir(exist_ok=True)

app = Flask(__name__)


def send_page(filename):
    return send_from_directory(PAGES_DIR, filename)


@app.route("/")
def index():
    return send_page("home.html")


@app.route("/search")
def search_wines():
    return send_page("searchwine.html")


@app.route("/camera")
def camera_page():
    return send_page("camera.html")


@app.route("/camera/verify/")
def verify():
    return send_page("verify.html")


@app.route("/scripts/<path:filename>")
def scripts(filename):
    return send_from_directory(SCRIPTS_DIR, filename)


@app.route("/assets/<path:filename>")
def assets(filename):
    return send_from_directory(ASSETS_DIR, filename)


@app.route("/wines")
def getwines():
    conn = dbmanager.connect()
    res = dbmanager.search_wines(conn, "", limit=5)
    conn.close()
    return jsonify({"wines": res})


@app.route("/upload-photo", methods=["POST"])
def upload_photo():
    if "photo" not in request.files:
        return jsonify({"message": "No photo file provided."}), 400

    photo = request.files["photo"]
    if photo.filename == "":
        return jsonify({"message": "No file name provided."}), 400

    filename = secure_filename(photo.filename) or "photo.png"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_name = f"{timestamp}_{filename}"
    save_path = UPLOAD_DIR / save_name
    photo.save(save_path)

    details = infer_wine_details.infer_basic(save_path, True)
    return jsonify({
        "message": "Photo saved successfully.",
        "filename": save_name.split(".png")[0],
        "name": details["name"],
        "year": details["year"],
        "grape_variety": details["grape_variety"],
        "region": details["region"],
    })


@app.route("/uploads/<path:filename>")
def serve_upload(filename):
    return send_from_directory(UPLOAD_DIR, filename)


@app.route("/add-to-cellar", methods=["POST"])
def add():
    data = request.get_json()
    try:
        infer_wine_details.Add_to_cellar(data)
        return jsonify({"status": "added"})
    except Exception:
        return jsonify({"status": "failed"}), 500


@app.route("/remove-from-cellar", methods=["POST"])
def remove():
    data = request.get_json()
    try:
        infer_wine_details.Remove_from_cellar(data)
        return jsonify({"status": "removed"})
    except Exception:
        return jsonify({"status": "failed"}), 500


def run_app():
    pem_path = os.environ.get("PEM_PATH")
    pem_dir = Path(pem_path) if pem_path else ROOT_DIR / "pem"
    ssl_context = (str(pem_dir / "cert.pem"), str(pem_dir / "key.pem"))
    app.run(host="0.0.0.0", port=5000, debug=True, ssl_context=ssl_context)


if __name__ == "__main__":
    run_app()

import os
from datetime import datetime
from pathlib import Path
import sys
from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory
from werkzeug.utils import secure_filename
import dbmanager
import infer_wine_details
import threading

BACKEND_DIR = Path(__file__).resolve().parent
ROOT_DIR = BACKEND_DIR.parent
FRONTEND_DIR = ROOT_DIR / "frontend"
PAGES_DIR = FRONTEND_DIR / "pages"
SCRIPTS_DIR = FRONTEND_DIR / "scripts"
ASSETS_DIR = FRONTEND_DIR / "assets"
UPLOAD_DIR = ROOT_DIR / "uploads"
localInfer = False
load_dotenv(ROOT_DIR / ".env")

UPLOAD_DIR.mkdir(exist_ok=True)

app = Flask(__name__)


def send_page(filename):
    return send_from_directory(PAGES_DIR, filename)


@app.route("/")
def index():
    return send_page("home.html")


@app.route("/apple-touch-icon.png")
@app.route("/apple-touch-icon-precomposed.png")
def apple_touch_icon():
    return send_from_directory(ASSETS_DIR / "images", "apple-touch-icon.png")

@app.route("/favicon.ico")
def favicon():
    return send_from_directory(ASSETS_DIR / "images", "favicon.ico")


@app.route("/search")
def search_wines():
    return send_page("searchwine.html")


@app.route("/pairings")
def search_pairings():
    return send_page("pairings.html")


@app.route("/view")
def view_wine():
    return send_page("viewwine.html")


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

@app.get("/wines")
def getwines():
    conn = dbmanager.connect()
    res = dbmanager.search_wines(conn, "", limit=5, in_cellar_only=1)
    conn.close()
    return jsonify({"wines": res})


@app.delete("/wines/<int:wineid>")
def delete_wine(wineid):
    conn = dbmanager.connect()
    res = dbmanager.remove_wine_from_cellar(conn, int(wineid), -1)
    conn.close()


    if res !=True:
        return jsonify({"message": "Failed to delete wine"}), 404

    return jsonify({"message": "Wine deleted successfully"})


@app.route("/wine/<int:wineid>")
def get_wine(wineid):
    conn = dbmanager.connect()
    res = dbmanager.get_wine_by_id(conn, wineid)
    conn.close()

    if res is None:
        return jsonify({"message": "Wine not found"}), 404

    return jsonify({"wine": res})

@app.post("/wine/<int:wineid>/general-data")
def update_general_data(wineid):
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()
    region = str(data.get("region", "")).strip()
    grapes = data.get("grapes",[])
    year = data.get("year", None)
    quantity = data.get("quantity", None)
    drink_start = data.get("drink_window_start", 0)
    drink_end = data.get("drink_window_end", 0)
    with open("debug_log.txt", "a") as f:
        f.write(f"Received data for wineid {wineid}: name={name}, region={region}, grapes={grapes}, year={year}, quantity={quantity}, drink_start={drink_start}, drink_end={drink_end}\n")
    conn = dbmanager.connect()
    updated_wine = dbmanager.update_general_data(conn, wineid, name, region, grapes, year, quantity, drink_start, drink_end)

    if updated_wine is None:
        return jsonify({"message": "Wine not found"}), 404


    res = dbmanager.get_wine_by_id(conn, wineid)
    conn.close()

    return jsonify({"wine": res}), 200

@app.post("/wine/<int:wineid>/custom-note")
def update_custom_notes(wineid):
    data = request.get_json(silent=True) or {}

    notes = str(data.get("note", "")).strip()

    conn = dbmanager.connect()
    updated_notes = dbmanager.update_custom_notes(conn, wineid, notes)
    conn.close()

    if updated_notes is None:
        return jsonify({"message": "Wine not found"}), 404

    return jsonify({"custom_notes": updated_notes})


@app.post("/wine/<int:wineid>/tasting-notes")
def add_tasting_note(wineid):
    data = request.get_json(silent=True) or {}
    note = str(data.get("note", "")).strip()

    if not note:
        return jsonify({"message": "Tasting note is required"}), 400

    conn = dbmanager.connect()
    notes = dbmanager.add_tasting_note(conn, wineid, note)
    conn.close()

    if notes is None:
        return jsonify({"message": "Wine not found"}), 404

    return jsonify({"tasting_notes": notes})


@app.delete("/wine/<int:wineid>/tasting-notes")
def delete_tasting_note(wineid):
    data = request.get_json(silent=True) or {}
    note = str(data.get("note", "")).strip()

    if not note:
        return jsonify({"message": "Tasting note is required"}), 400

    conn = dbmanager.connect()
    notes = dbmanager.remove_tasting_note(conn, wineid, note)
    conn.close()

    if notes is None:
        return jsonify({"message": "Wine not found"}), 404

    return jsonify({"tasting_notes": notes})


@app.post("/wine/<int:wineid>/pairings")
def add_wine_pairing(wineid):
    data = request.get_json(silent=True) or {}
    pairing = str(data.get("pairing", "")).strip()

    if not pairing:
        return jsonify({"message": "Pairing is required"}), 400

    conn = dbmanager.connect()
    pairings = dbmanager.add_pairing_to_wine(conn, wineid, pairing)
    conn.close()

    if pairings is None:
        return jsonify({"message": "Wine not found"}), 404

    return jsonify({"pairings": pairings})


@app.delete("/wine/<int:wineid>/pairings")
def delete_wine_pairing(wineid):
    data = request.get_json(silent=True) or {}
    pairing = str(data.get("pairing", "")).strip()

    if not pairing:
        return jsonify({"message": "Pairing is required"}), 400

    conn = dbmanager.connect()
    pairings = dbmanager.remove_pairing_from_wine(conn, wineid, pairing)
    conn.close()

    if pairings is None:
        return jsonify({"message": "Wine not found"}), 404

    return jsonify({"pairings": pairings})


@app.route("/pairing-wines")
def get_pairing_wines():
    pairing = request.args.get("q", "")
    conn = dbmanager.connect()
    res = dbmanager.search_wines_by_pairing(conn, pairing, limit=20)
    conn.close()
    return jsonify({"wines": res})


@app.route("/upload-photo", methods=["POST"])
def upload_photo():
    if request.args.get("test_error") == "1":
        return jsonify({
            "message": "Test error: upload failed on purpose so you can verify the popup.",
        }), 500

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

    try:
        details = infer_wine_details.infer_basic(save_path, False, local=localInfer)
    except Exception:
        return jsonify({
            "message": "The image could not be analyzed. Please try a clearer wine photo.",
        }), 500

    return jsonify({
        "message": "Photo saved successfully.",
        "filename": save_name.split(".png")[0],
        "name": details["name"],
        "year": details["year"],
        "grape_variety": details["grape_variety"],
        "region": details["region"],
        "imgpath": save_name
    })


@app.route("/uploads/<path:filename>")
def serve_upload(filename):
    return send_from_directory(UPLOAD_DIR, filename)


@app.route("/add-to-cellar", methods=["POST"])
def add():
    data = request.get_json()
    print(data)
    try:
        thread = threading.Thread(target=infer_wine_details.Add_to_cellar, args=(data,))
        #infer_wine_details.Add_to_cellar(data)
        thread.start()
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
    if len(sys.argv) > 1 and sys.argv[1] == "--local":
        localInfer = True

    run_app()

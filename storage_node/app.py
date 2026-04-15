from flask import Flask, request, send_file, jsonify
import os

app = Flask(__name__)
STORAGE_DIR = "data"

os.makedirs(STORAGE_DIR, exist_ok=True)

@app.route("/store", methods=["POST"])
def store():
    shard_id = request.form["shard_id"]
    file = request.files["file"]

    path = os.path.join(STORAGE_DIR, shard_id)
    file.save(path)

    return jsonify({"status": "stored", "shard_id": shard_id})


@app.route("/retrieve/<shard_id>", methods=["GET"])
def retrieve(shard_id):
    path = os.path.join(STORAGE_DIR, shard_id)

    if not os.path.exists(path):
        return jsonify({"error": "not found"}), 404

    return send_file(path, as_attachment=True)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/")
def home():
    return "Storage Node Running 📦"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
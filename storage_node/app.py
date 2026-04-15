from flask import Flask, request, send_file, jsonify
import os
import argparse

app = Flask(__name__)

# Will be set per-instance based on port (e.g. data_5001)
STORAGE_DIR = "data"


@app.route("/store", methods=["POST"])
def store():
    if "shard_id" not in request.form or "file" not in request.files:
        return jsonify({"error": "missing data"}), 400

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
    return jsonify({"status": "ok", "storage": STORAGE_DIR})


@app.route("/")
def home():
    return f"Storage Node Running 📦 (Storage: {STORAGE_DIR})"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=5000)
    args = parser.parse_args()

    # Each node gets its own isolated data directory (e.g. data_5001)
    # This is CRITICAL when running multiple nodes on the same machine
    STORAGE_DIR = f"data_{args.port}"
    os.makedirs(STORAGE_DIR, exist_ok=True)

    app.run(host="0.0.0.0", port=args.port)
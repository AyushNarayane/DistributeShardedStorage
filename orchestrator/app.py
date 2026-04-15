from flask import Flask, request, send_file, jsonify, render_template
import requests
import os
from db import init_db, insert_shard, get_shards
from shard import split_file, merge_file, checksum

app = Flask(__name__)

# 🔥 CHANGE THESE IPs
NODES = [
    "http://192.168.137.200:5001",
    "http://192.168.137.109:5002",
   # "http://192.168.137.117:5003"
]

init_db()

@app.route("/upload", methods=["POST"])
def upload():
    file = request.files["file"]
    data = file.read()
    file_id = file.filename

    # Split dynamically based on available nodes
    shards = split_file(data, len(NODES))

    for i, shard in enumerate(shards):
        shard_id = f"{file_id}_part{i}"
        
        # Round-robin selection if shards > nodes
        node_url = NODES[i % len(NODES)]

        try:
            requests.post(
                f"{node_url}/store",
                files={"file": (shard_id, shard)},
                data={"shard_id": shard_id}
            )

            insert_shard(file_id, shard_id, node_url, checksum(shard))

        except Exception as e:
            print(f"Error {e}")
            return jsonify({"error": f"Node {node_url} down"}), 500

    return jsonify({"status": "uploaded"})


@app.route("/download/<file_id>", methods=["GET"])
def download(file_id):
    rows = get_shards(file_id)

    if not rows:
        return jsonify({"error": "file not found"}), 404

    shards = []

    for shard_id, node, chksum in rows:
        try:
            res = requests.get(f"{node}/retrieve/{shard_id}")
            data = res.content

            if checksum(data) != chksum:
                return jsonify({"error": "corrupted shard"})

            shards.append(data)

        except Exception as e:
            return jsonify({"error": "node failure"})

    final_data = merge_file(shards)

    path = f"temp_{file_id}"
    with open(path, "wb") as f:
        f.write(final_data)

    return send_file(path, as_attachment=True)


STORAGE_DIR = "storage"
if not os.path.exists(STORAGE_DIR):
    os.makedirs(STORAGE_DIR)

@app.route("/store", methods=["POST"])
def store_shard():
    file = request.files["file"]
    shard_id = request.form["shard_id"]
    filepath = os.path.join(STORAGE_DIR, shard_id)
    file.save(filepath)
    return jsonify({"status": "stored"})

@app.route("/retrieve/<shard_id>", methods=["GET"])
def retrieve_shard(shard_id):
    filepath = os.path.join(STORAGE_DIR, shard_id)
    if os.path.exists(filepath):
        return send_file(filepath)
    return jsonify({"error": "not found"}), 404


@app.route("/")
def home():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
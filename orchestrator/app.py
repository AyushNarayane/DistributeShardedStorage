from flask import Flask, request, send_file, jsonify, render_template
import requests
import os
import uuid
import io
from db import init_db, insert_upload, insert_shard, get_upload, get_shards, get_all_uploads
from shard import split_file, merge_file, checksum, compute_parity, recover_shard
from crypto import encrypt_data, decrypt_data

app = Flask(__name__)

# 🔥 CHANGE THESE IPs to your local machine IPs
NODES = [
    "http://127.0.0.1:5001",
    "http://127.0.0.1:5002",
]

init_db()


@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
        
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    raw_data = file.read()
    file_name = file.filename

    try:
        # Step 1: Encrypt the file data
        encrypted_data = encrypt_data(raw_data)
        original_size = len(encrypted_data)

        # Step 2: Generate unique upload ID
        upload_id = str(uuid.uuid4())[:8]

        # Step 3: RAID 5 logic
        num_nodes = len(NODES)
        if num_nodes < 1:
            return jsonify({"error": "No storage nodes configured"}), 500

        if num_nodes >= 2:
            num_data_shards = num_nodes - 1
            data_shards = split_file(encrypted_data, num_data_shards)
            parity_shard = compute_parity(data_shards)
            all_shards = data_shards + [parity_shard]
        else:
            # Single node fallback
            data_shards = split_file(encrypted_data, 1)
            all_shards = data_shards

        # Step 4: Metadata storage
        insert_upload(upload_id, file_name, original_size)

        # Step 5: Distribute shards
        for i, shard in enumerate(all_shards):
            is_parity = 1 if (num_nodes >= 2 and i == len(data_shards)) else 0
            shard_id = f"{upload_id}_part{i}"
            node_url = NODES[i % num_nodes]

            requests.post(
                f"{node_url}/store",
                files={"file": (shard_id, shard)},
                data={"shard_id": shard_id},
                timeout=5
            )
            insert_shard(upload_id, shard_id, i, node_url, checksum(shard), is_parity)

        return jsonify({
            "status": "uploaded",
            "upload_id": upload_id,
            "file_name": file_name,
            "shards": len(data_shards),
            "parity": 1 if num_nodes >= 2 else 0
        })

    except Exception as e:
        print(f"Upload failed: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/download/<upload_id>", methods=["GET"])
def download(upload_id):
    upload_info = get_upload(upload_id)
    if not upload_info:
        return jsonify({"error": "File not found"}), 404

    _, file_name, original_size = upload_info
    rows = get_shards(upload_id)

    shard_data = {}
    parity_data = None
    failed_indices = []

    # Determine parity index from DB metadata BEFORE fetching
    # This ensures we know which shard is parity even if its node is down
    parity_index = -1
    for _, shard_index, _, _, is_parity in rows:
        if is_parity:
            parity_index = shard_index
            break

    # Fetch shards
    for shard_id, shard_index, node, chksum, is_parity in rows:
        try:
            res = requests.get(f"{node}/retrieve/{shard_id}", timeout=5)
            if res.status_code != 200:
                raise Exception(f"Node returned {res.status_code}")

            data = res.content
            if checksum(data) != chksum:
                raise Exception("Checksum mismatch")

            if is_parity:
                parity_data = data
            else:
                shard_data[shard_index] = data

        except Exception as e:
            print(f"Shard {shard_index} fetch error: {e}")
            failed_indices.append(shard_index)

    # Recovery logic — filter out parity from failed list
    failed_data_shards = [i for i in failed_indices if i != parity_index]

    if len(failed_data_shards) > 1:
        return jsonify({"error": "Multiple node failure. Data unrecoverable."}), 500

    if len(failed_data_shards) == 1:
        if parity_data is not None:
            missing_idx = failed_data_shards[0]
            # Get sorted list of available data shards
            available = [shard_data[i] for i in sorted(shard_data.keys())]
            recovered = recover_shard(available, parity_data)
            shard_data[missing_idx] = recovered
        else:
            return jsonify({"error": "Missing data + missing parity = unrecoverable"}), 500

    # Reassemble and Decrypt
    ordered_shards = [shard_data[i] for i in sorted(shard_data.keys())]
    try:
        encrypted_data = merge_file(ordered_shards, original_size)
        decrypted_data = decrypt_data(encrypted_data)
        
        # USE BytesIO to avoid Windows file-locking issues
        return send_file(
            io.BytesIO(decrypted_data),
            as_attachment=True,
            download_name=file_name,
            mimetype='application/octet-stream'
        )
    except Exception as e:
        return jsonify({"error": f"Reassembly/Decryption failed: {e}"}), 500


@app.route("/files", methods=["GET"])
def list_files():
    uploads = get_all_uploads()
    return jsonify({
        "files": [
            {"upload_id": r[0], "file_name": r[1], "size": r[2], "upload_time": r[3]} 
            for r in uploads
        ]
    })


@app.route("/nodes", methods=["GET"])
def list_nodes():
    node_status = []
    for node in NODES:
        try:
            res = requests.get(f"{node}/health", timeout=2)
            if res.status_code == 200:
                node_status.append({"url": node, "status": "online", "details": res.json()})
            else:
                node_status.append({"url": node, "status": "error", "code": res.status_code})
        except Exception as e:
            node_status.append({"url": node, "status": "offline", "error": str(e)})
    
    return jsonify({"nodes": node_status})


@app.route("/")
def home():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
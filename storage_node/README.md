# 📦 Storage Node

Lightweight worker that stores and serves encrypted shard files for the Distributed Sharded Storage system.

## What it does
- **`POST /store`** — Receives an encrypted shard from the Orchestrator and saves it to disk.
- **`GET /retrieve/<shard_id>`** — Returns a stored shard back to the Orchestrator.
- **`GET /health`** — Health check endpoint.

## Running

```bash
# Each node must use a unique port
python app.py --port 5001
python app.py --port 5002
```

Each instance creates its own isolated data folder (`data_5001/`, `data_5002/`), so multiple nodes can safely run on the same machine.

## Security
This node does **not** handle encryption or decryption. It only stores opaque encrypted blobs provided by the Orchestrator. It has no knowledge of the original file content or the master key.

## Requirements
```
flask
```

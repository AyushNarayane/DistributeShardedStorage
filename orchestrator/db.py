import sqlite3

DB = "metadata.db"


def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    # Uploads table — one row per upload (unique upload_id per upload)
    c.execute("""
    CREATE TABLE IF NOT EXISTS uploads (
        upload_id TEXT PRIMARY KEY,
        file_name TEXT,
        original_size INTEGER,
        upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Shards table — one row per shard (data + parity)
    c.execute("""
    CREATE TABLE IF NOT EXISTS shards (
        upload_id TEXT,
        shard_id TEXT,
        shard_index INTEGER,
        node TEXT,
        checksum TEXT,
        is_parity INTEGER DEFAULT 0,
        FOREIGN KEY (upload_id) REFERENCES uploads(upload_id)
    )
    """)

    conn.commit()
    conn.close()


def insert_upload(upload_id, file_name, original_size):
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("INSERT INTO uploads VALUES (?,?,?, CURRENT_TIMESTAMP)",
              (upload_id, file_name, original_size))

    conn.commit()
    conn.close()


def insert_shard(upload_id, shard_id, shard_index, node, checksum, is_parity=0):
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("INSERT INTO shards VALUES (?,?,?,?,?,?)",
              (upload_id, shard_id, shard_index, node, checksum, is_parity))

    conn.commit()
    conn.close()


def get_upload(upload_id):
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("SELECT upload_id, file_name, original_size FROM uploads WHERE upload_id=?",
              (upload_id,))
    row = c.fetchone()

    conn.close()
    return row


def get_shards(upload_id):
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""SELECT shard_id, shard_index, node, checksum, is_parity
                 FROM shards WHERE upload_id=? ORDER BY shard_index""",
              (upload_id,))
    rows = c.fetchall()

    conn.close()
    return rows


def get_all_uploads():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""SELECT upload_id, file_name, original_size, upload_time
                 FROM uploads ORDER BY upload_time DESC""")
    rows = c.fetchall()

    conn.close()
    return rows
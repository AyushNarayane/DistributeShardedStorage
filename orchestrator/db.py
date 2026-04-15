import sqlite3

DB = "metadata.db"

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS files (
        file_id TEXT,
        shard_id TEXT,
        node TEXT,
        checksum TEXT
    )
    """)

    conn.commit()
    conn.close()


def insert_shard(file_id, shard_id, node, checksum):
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("INSERT INTO files VALUES (?,?,?,?)",
              (file_id, shard_id, node, checksum))

    conn.commit()
    conn.close()


def get_shards(file_id):
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("SELECT shard_id, node, checksum FROM files WHERE file_id=?", (file_id,))
    rows = c.fetchall()

    conn.close()
    return rows
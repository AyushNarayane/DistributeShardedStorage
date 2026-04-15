import hashlib

def split_file(data, n):
    size = len(data) // n
    return [data[i*size:(i+1)*size] for i in range(n-1)] + [data[(n-1)*size:]]

def merge_file(shards):
    return b"".join(shards)

def checksum(data):
    return hashlib.sha256(data).hexdigest()
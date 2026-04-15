import hashlib


def split_file(data, num_data_shards):
    """Split data into equal-sized shards, padding last shard if needed.

    All shards must be the same size for XOR parity computation.
    """
    if num_data_shards <= 0:
        raise ValueError("Number of data shards must be positive")

    shard_size = (len(data) + num_data_shards - 1) // num_data_shards
    shards = []

    for i in range(num_data_shards):
        start = i * shard_size
        end = start + shard_size
        shard = data[start:end]

        # Pad last shard to equal size for parity computation
        if len(shard) < shard_size:
            shard = shard + b'\x00' * (shard_size - len(shard))

        shards.append(shard)

    return shards


def compute_parity(shards):
    """Compute XOR parity across all data shards (RAID 5).

    Parity P = S0 XOR S1 XOR S2 XOR ... XOR Sn
    """
    shard_size = len(shards[0])
    parity = bytearray(shard_size)

    for shard in shards:
        for j in range(shard_size):
            parity[j] ^= shard[j]

    return bytes(parity)


def recover_shard(available_shards, parity):
    """Recover a missing shard using XOR of available shards and parity.

    If P = S0 ^ S1 ^ S2, then:
        S1 = P ^ S0 ^ S2  (XOR parity with all OTHER available shards)
    """
    shard_size = len(parity)
    recovered = bytearray(parity)

    for shard in available_shards:
        for j in range(shard_size):
            recovered[j] ^= shard[j]

    return bytes(recovered)


def merge_file(shards, original_size):
    """Merge shards and trim to original size (removes padding)."""
    return b"".join(shards)[:original_size]


def checksum(data):
    """Compute SHA-256 checksum."""
    return hashlib.sha256(data).hexdigest()
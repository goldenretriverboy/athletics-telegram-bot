import hashlib


def stable_hash(value: str) -> str:
    normalized = " ".join(value.strip().split()).lower()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


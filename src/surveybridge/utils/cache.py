"""Content-addressed cache with original retrieval times and integrity checks."""

import hashlib
import json
import os
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path


def canonical(value) -> bytes:
    return json.dumps(
        value, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(",", ":")
    ).encode("utf-8")


def digest(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def atomic_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(dir=path.parent, prefix=".write-", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(canonical(value))
        for attempt in range(6):
            try:
                os.replace(temp, path)
                break
            except PermissionError:
                if attempt == 5:
                    raise
                time.sleep(0.05 * (attempt + 1))
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


class ResponseCache:
    def __init__(self, root: Path):
        self.root = root

    def get(self, url: str, ttl: int, offline: bool = False):
        path = self.root / (digest(url.encode()) + ".json")
        if not path.exists():
            return None
        item = json.loads(path.read_text(encoding="utf-8"))
        if item["url"] != url or digest(bytes.fromhex(item["body_hex"])) != item["sha256"]:
            raise ValueError("Cached response failed integrity verification")
        age = (datetime.now(UTC) - datetime.fromisoformat(item["retrieved_utc"])).total_seconds()
        return item if offline or age <= ttl else None

    def put(self, url: str, body: bytes):
        item = {
            "url": url,
            "body_hex": body.hex(),
            "sha256": digest(body),
            "retrieved_utc": datetime.now(UTC).isoformat(),
        }
        atomic_json(self.root / (digest(url.encode()) + ".json"), item)
        return item

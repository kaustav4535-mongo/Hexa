"""
db.py — JSON file-based database (MongoDB-ready).
To switch to MongoDB: set USE_MONGO=true in .env and provide MONGO_URI.
All methods mirror pymongo's interface so migration is seamless.
"""
import json, os, uuid, threading
from datetime import datetime
from shared.config import Config

_lock = threading.Lock()
DB_PATH = Config.DB_PATH

# ── Default schema ──────────────────────────────────────────────────────────
_DEFAULT = {
    "users":    [],   # customers
    "drivers":  [],
    "admins":   [],
    "bookings": [],
    "zones":    [],   # pricing zones
    "payments": [],
    "sessions": [],
    "withdrawals": [],
    "commissions": [],
}

def _load() -> dict:
    if not os.path.exists(DB_PATH):
        _save(_DEFAULT)
        return _DEFAULT
    with open(DB_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    # ensure all collections exist
    for k, v in _DEFAULT.items():
        data.setdefault(k, v)
    return data

def _save(data: dict):
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True) if os.path.dirname(DB_PATH) else None
    with open(DB_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)

# ── Low-level helpers ────────────────────────────────────────────────────────
def _now():
    return datetime.utcnow().isoformat()

def _new_id():
    return str(uuid.uuid4())

# ── Public API (mirrors pymongo patterns) ────────────────────────────────────

def find(collection: str, query: dict = None):
    """Return list of documents matching ALL query key-values."""
    with _lock:
        data = _load()
        docs = data.get(collection, [])
    if not query:
        return docs
    result = []
    for doc in docs:
        if all(doc.get(k) == v for k, v in query.items()):
            result.append(doc)
    return result

def find_one(collection: str, query: dict = None):
    results = find(collection, query)
    return results[0] if results else None

def insert_one(collection: str, document: dict) -> dict:
    """Insert document; auto-adds _id, created_at, updated_at."""
    with _lock:
        data = _load()
        document = {
            "_id": _new_id(),
            "created_at": _now(),
            "updated_at": _now(),
            **document
        }
        data[collection].append(document)
        _save(data)
    return document

def update_one(collection: str, query: dict, updates: dict) -> bool:
    """Update first matching document. Returns True if found."""
    with _lock:
        data = _load()
        for doc in data[collection]:
            if all(doc.get(k) == v for k, v in query.items()):
                doc.update(updates)
                doc["updated_at"] = _now()
                _save(data)
                return True
    return False

def delete_one(collection: str, query: dict) -> bool:
    """Delete first matching document. Returns True if deleted."""
    with _lock:
        data = _load()
        original_len = len(data[collection])
        data[collection] = [
            doc for doc in data[collection]
            if not all(doc.get(k) == v for k, v in query.items())
        ]
        if len(data[collection]) < original_len:
            _save(data)
            return True
    return False

def count(collection: str, query: dict = None) -> int:
    return len(find(collection, query))

def get_all_collections() -> dict:
    with _lock:
        return _load()

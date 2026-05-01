"""
db.py — JSON file-based database (MongoDB-ready).
To switch to MongoDB: set USE_MONGO=true in .env and provide MONGO_URI.
All methods mirror pymongo's interface so migration is seamless.
"""
import json, os, uuid, threading
from datetime import datetime
from shared.config import Config

try:
    from pymongo import MongoClient
except Exception:
    MongoClient = None

_lock = threading.Lock()
DB_PATH = Config.DB_PATH

_use_mongo = bool(Config.USE_MONGO and Config.MONGO_URI and MongoClient)
_mongo = None
if Config.USE_MONGO and not _use_mongo:
    print("[DB] USE_MONGO enabled but MongoClient/MONGO_URI missing — falling back to JSON DB.")
if _use_mongo:
    _mongo = MongoClient(Config.MONGO_URI)[Config.MONGO_DB_NAME]

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

def _normalize_doc(doc: dict | None) -> dict | None:
    if not doc:
        return doc
    doc = dict(doc)
    if "_id" in doc and not isinstance(doc["_id"], str):
        doc["_id"] = str(doc["_id"])
    return doc

# ── Public API (mirrors pymongo patterns) ────────────────────────────────────

def find(collection: str, query: dict = None):
    """Return list of documents matching ALL query key-values."""
    if _use_mongo:
        docs = list(_mongo[collection].find(query or {}))
        return [_normalize_doc(d) for d in docs]
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
    if _use_mongo:
        return _normalize_doc(_mongo[collection].find_one(query or {}))
    results = find(collection, query)
    return results[0] if results else None

def insert_one(collection: str, document: dict) -> dict:
    """Insert document; auto-adds _id, created_at, updated_at."""
    if _use_mongo:
        document = {
            "_id": _new_id(),
            "created_at": _now(),
            "updated_at": _now(),
            **document
        }
        _mongo[collection].insert_one(document)
        return document
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
    if _use_mongo:
        updates = {**updates, "updated_at": _now()}
        result = _mongo[collection].update_one(query, {"$set": updates})
        return result.matched_count > 0
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
    if _use_mongo:
        result = _mongo[collection].delete_one(query)
        return result.deleted_count > 0
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
    if _use_mongo:
        return _mongo[collection].count_documents(query or {})
    return len(find(collection, query))

def get_all_collections() -> dict:
    if _use_mongo:
        return {name: find(name) for name in _DEFAULT.keys()}
    with _lock:
        return _load()

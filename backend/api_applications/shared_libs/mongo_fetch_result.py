import logging
import os
from typing import Any, Optional
from dotenv import load_dotenv
from .monogo_connections import connect_monogo

load_dotenv()

_COLLECTION = os.getenv("MONGO_COLLECTION")


def get_collection(name):
    db = connect_monogo()
    if db is not None:
        return db.get_collection(name)
    else:
        raise Exception("connect_mongo() returned None (DB connection failed)")


def fetch_by_ip(ip: str) -> Optional[dict[str, Any]]:
    try:
        collection = get_collection(_COLLECTION)
        return collection.find_one({"_id": ip})
    except Exception as e:
        logging.info(f"[mongo_fetch_result] ERROR: {e}")

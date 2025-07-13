import logging
import os
from urllib.parse import quote_plus

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure

MONGO_HOST = os.getenv("MONGO_HOST")
MONGO_PORT = int(os.getenv("MONGO_PORT"))
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")
MONGO_USERNAME = os.getenv("MONGO_USERNAME")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD")
MONGO_AUTH_DB = os.getenv("MONGO_AUTH_DB")

_client = None
_db = None

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)


def connect_monogo():
    global _client, _db
    if _client is None:
        try:
            username_escaped = quote_plus(MONGO_USERNAME)
            password_escaped = quote_plus(MONGO_PASSWORD)
            mongo_uri = (
                f"mongodb://{username_escaped}:{password_escaped}"
                f"@{MONGO_HOST}:{MONGO_PORT}/?authSource={MONGO_AUTH_DB}"
            )
            _client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
            _client.admin.command("ping")
            _db = _client[MONGO_DB_NAME]
            logging.info(
                f"[db_operation.py] Connected to MongoDB at {MONGO_HOST}:{MONGO_PORT}, DB={MONGO_DB_NAME}"
            )
        except ConnectionFailure as e:
            logging.info(f"[db_operation.py] ERROR: Could not connect to MongoDB: {e}")
            _client = None
            raise
        except OperationFailure as e:
            logging.info(
                f"[db_operation.py] ERROR: MongoDB operation/authentication failed: {e}"
            )
            _client = None
            raise
        except Exception as e:
            logging.info(
                f"[db_operation.py] ERROR: Unexpected exception on MongoDB connection: {e}"
            )
            _client = None
            raise
    return _db


def close_db_connection():

    global _client
    if _client:
        _client.close()
        logging.info("[db_operation.py] MongoDB connection closed.")
        _client = None

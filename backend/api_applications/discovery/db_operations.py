import logging
import time
from pymongo import UpdateOne

from shared_libs import monogo_connections


def check_connection():
    while True:
        
        try:
            monogo_connections.connect_monogo()
            break
        
        except Exception as e:
            logging.info(f"[!] Waiting for MongoDB... {e}")
            time.sleep(3)


def insert_many_scan_result(data: list):

    try:
        db = monogo_connections.connect_monogo()
        result = db.scan_results.insert_many(data)
        logging.info(
            f"[db_operation.py] Data inserted with ID")
        return result.inserted_ids

    except Exception as e:
        logging.error(
            f"[db_operation.py] ERROR: Failed to insert data into MongoDB: {e}"
        )
        return None


def is_exists(data: str):
    try:

        db = monogo_connections.connect_monogo()
        result = db.scan_results.find_one({"_id": data})
        logging.info(f"in db_operation {result}")
        return result is not None
    except Exception as e:
        logging.error(
            f"[db_operation.py] ERROR: Failed to find data into MongoDB: {e}")
        return False


def update_scan_result(data: list):
    try:
        db = monogo_connections.connect_monogo()
        operations = []
        for doc in data:
            operations.append(
                UpdateOne(
                    {"_id": doc["_id"]},
                    {
                        "$set": {
                            "ports": doc["ports"],
                            "last_update": doc["last_update"]
                        },
                        "$unset": {
                            "finger_print": "",
                            "general": "",
                            "domain": "",
                            "service_type": "",
                            "vulnerability": "",
                        },
                    },
                    upsert=True,
                )
            )
        if operations:
            result = db.scan_results.bulk_write(operations, ordered=False)
            logging.info(f"Flushed {len(operations)} updates in one batch to db")
        return True
    except Exception as e:
        logging.error(f"[db_operation.py] ERROR: Failed to bulk update data : {e}")
        return None


def find_down_ips():
    try:

        db = monogo_connections.connect_monogo()
        if db is None:
            logging.error(
                "Cannot connect to MongoDB: connect_monogo() returned None")
            return None
        results = db.scan_results.find({"ports": []})
        down_ips = list(results)
        logging.info(down_ips)
        return down_ips
    except Exception as e:
        logging.info(f"[db_operation.py] ERROR: Failed to find data : {e}")

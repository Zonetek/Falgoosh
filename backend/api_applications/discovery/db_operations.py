import logging
import time

from ..shared_libs import monogo_connections

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)


def check_connection():
    while True:
        try:
            monogo_connections.connect_monogo()
            break
        except Exception as e:
            logging.info(f"[!] Waiting for MongoDB... {e}")
            time.sleep(3)


def insert_scan_result(data: dict):
    try:
        db = monogo_connections.connect_monogo()
        result = db.scan_results.insert_one(data)
        logging.info(f"[db_operation.py] Data inserted with ID: {result.inserted_id}")
        return result.inserted_id
    except Exception as e:
        logging.info(
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
        logging.info(f"[db_operation.py] ERROR: Failed to find data into MongoDB: {e}")
        return False


def update_scan_result(data: dict):
    try:
        db = monogo_connections.connect_monogo()
        logging.info(f"the data in update is {data}")
        result = db.scan_results.update_one(
            {"_id": data["_id"]},
            {"$set": {"ports": data["ports"], "last_update": data["last_update"]},
            
                "$unset": {
                    "finger_print": "",
                    "general": "",
                    "domain": "",
                    "service_type": "",
                    "vulnerability": ""
                }
            },
            upsert=True 
        )
        return True
    except Exception as e:
        logging.info(f"[db_operation.py] ERROR: Failed to update data : {e}")
        return None


def find_down_ips():
    try:

        db = monogo_connections.connect_monogo()
        if db is None:
            logging.error("Cannot connect to MongoDB: connect_monogo() returned None")
            return None
        results = db.scan_results.find({"ports": []})
        down_ips = list(results)
        logging.info(down_ips)
        return down_ips
    except Exception as e:
        logging.info(f"[db_operation.py] ERROR: Failed to find data : {e}")

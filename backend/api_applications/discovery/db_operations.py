from shared_libs import monogo_connections


def insert_scan_result(data: dict):
    try:
        db = monogo_connections.connect_monogo()
        result = db.scan_results.insert_one(data)
        print(f"[db_operation.py] Data inserted with ID: {result.inserted_id}")
        return result.inserted_id
    except Exception as e:
        print(f"[db_operation.py] ERROR: Failed to insert data into MongoDB: {e}")
        return None


def close_db_connection():

    global _client
    if _client:
        _client.close()
        print("[db_operation.py] MongoDB connection closed.")
        _client = None

import logging

from shared_libs import monogo_connections

from banner_grabbing import finger_print


def update_results():
    try:
        db = monogo_connections.connect_monogo()
        results = list(db.scan_results.find({"finger_print": {"$exists": False}}))
        
        for i in results:
            logging.info(f"getting OS finger print of : {i}")
            f_p = finger_print.os_finger_print(i["ip"])
            logging.info(f"test {f_p}")
            db.scan_results.update_one(
                {"ip": i["ip"]},
                {"$set": {"finger_print": f_p}},
            )
            return f"{len(results)} updated"
    except Exception as e:
        print(f"Operation do not complete : {e}")
        return None

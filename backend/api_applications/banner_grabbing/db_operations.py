import logging

from shared_libs import monogo_connections

from . import banner_grabber, vulnerability


def update_banners():

    try:
        db = monogo_connections.connect_monogo()
        results = list(
            db.scan_results.find(
                {
                    "service_type": {"$exists": False},
                    "ports": {"$exists": True, "$nin": [[], None]},
                }
            )
        )
        for i in results:
            banner = banner_grabber.scan_ports_for_banners(i["_id"], i["ports"])
            logging.info(f"Updating banner, result is: {banner}")
            logging.info(f"getting SERVICE TYPE of : {i}")
            db.scan_results.update_one(
                {"_id": i["_id"]}, {"$set": {"service_type": banner}}
            )
    
    except Exception as e:
        logging.error(f"Operation do not complete in update banner : {e}")


def update_vulnerability():

    try:
        db = monogo_connections.connect_monogo()
        results = list(
            db.scan_results.find(
                {
                    "vulnerability": {"$exists": False},
                    "service_type": {"$exists": True, "$ne": None},
                    "ports": {"$exists": True, "$nin": [[], None]},
                }
            )
        )
        try:

            for i in results:
                vul = vulnerability.get_vul(i["service_type"])
                if vul:
                    logging.info(f"Updating vuls, result is: {vul}")
                    logging.info(f"getting vuls of : {i}")
                    db.scan_results.update_one(
                        {"_id": i["_id"]}, {"$set": {"vulnerability": vul}}
                    )
        
        except Exception as e:
            logging.error(f"Operation do not complete in vuls : {e}")
    
    except Exception as e:
        logging.error(f"Operation do not complete in vuls : {e}")

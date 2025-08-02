import logging

from shared_libs import monogo_connections

from . import banner_grabber
from . import producer


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
            banner = banner_grabber.scan_ports_for_banners(
                i["_id"], i["ports"])
            logging.info(f"Updating banner, result is: {banner}")
            logging.info(f"getting SERVICE TYPE of : {i}")
            db.scan_results.update_one(
                {"_id": i["_id"]}, {"$set": {"service_type": banner}}
            )

            try:
                producer.producer_queue(str(banner))

            except Exception as e:
                logging.error(f"Falid to put banner in queue {e}")

    except Exception as e:
        logging.error(f"Operation do not complete in update banner : {e}")

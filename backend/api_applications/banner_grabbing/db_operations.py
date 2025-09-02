import logging

from shared_libs import monogo_connections
from pymongo import UpdateOne

from . import banner_grabber
from . import banner_producer

def update_banners(results):

    try:
        db = monogo_connections.connect_monogo()
        operations = []
        batches_to_send = []
        for i in results:
            if i["ports"]:
                banner = banner_grabber.scan_ports_for_banners(
                    i["_id"], i["ports"]
                )
                operations.append(
                    UpdateOne(
                        {"_id": i["_id"]},
                        {
                            "$set": {
                                "service_type": banner
                            }
                        },
                        upsert=True,
                    )
                )
                batches_to_send.append({
                    "_id": i["_id"],
                    "service_type": banner
                })

        if operations:
            result = db.scan_results.bulk_write(operations, ordered=False)
            banner_producer.send_vuln_batches(batches_to_send)
            logging.info(f"Flushed {operations}\n updates in one batch to db")

    except Exception as e:
        logging.error(f"Operation do not complete in update banner : {e}")

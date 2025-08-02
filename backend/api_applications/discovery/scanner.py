import ipaddress
import logging
import threading
import time
from datetime import datetime
import os

from . import port_scanner
from . import db_operations
from shared_models.schema import ScanResult

BATCH_SIZE = int(os.getenv("BATCH_SIZE", "250"))


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)


def generate_public_ipv4_ranges_stream(cidr_prefix=24):
    all_space = ipaddress.IPv4Network("0.0.0.0/0")
    for subnet in all_space.subnets(new_prefix=cidr_prefix):
        if subnet.is_global and not (
            subnet.is_private
            or subnet.is_loopback
            or subnet.is_link_local
            or subnet.is_multicast
            or subnet.is_reserved
        ):
            yield str(subnet)


def daily_scan():
    from . import db_operations
    insert_batch = []
    update_batch = []
    while True:
        for ip_range in generate_public_ipv4_ranges_stream(24):
            logging.info(f"Scanning: {ip_range}")
            result = port_scanner.call_ip_range(ip_range)
            for ip, ports in result:
                now = datetime.now()
                if db_operations.is_exists(ip):
                    logging.info(f"{ip} is already exists")
                    scan_data = {"_id": ip, "ports": ports, "last_update": now}
                    update_batch.append(scan_data)
                else:
                    scan_result = ScanResult(
                        _id=ip, ports=ports, last_update=now)
                    
                    insert_batch.append(scan_result.model_dump(by_alias=True, exclude_none=True))
                    logging.info(f"{insert_batch} apended")
                
                if len(insert_batch)+ len(update_batch) >= BATCH_SIZE:
                    if insert_batch:
                        try:
                            db_operations.insert_many_scan_result(insert_batch)
                            logging.info(f"Flushed {len(insert_batch)} documents to disk")
                            insert_batch = []
                        except Exception as e:
                            logging.error(f"ERROR:{e} \ncan not Flushed {len(insert_batch)} documents to disk")

                    if update_batch:
                        try:
                            logging.info(f"scanner.py data looks like{update_batch}")
                            db_operations.update_scan_result(update_batch)
                            logging.info(f"Flushed {len(update_batch)} documents to disk")
                            update_batch = []
                        except Exception as e:
                            logging.error(f"ERROR:{e} \ncan not Flushed {len(update_batch)} documents to disk")
                    
            if len(insert_batch)+ len(update_batch) > 0:
                if insert_batch:
                        db_operations.insert_many_scan_result(insert_batch)
                        logging.info(f"Flushed {len(insert_batch)} documents to disk")
                        insert_batch = []
                if update_batch:
                        db_operations.update_scan_result(update_batch)
                        logging.info(f"Flushed {len(update_batch)} documents to disk")
                        update_batch = []
        logging.info(
            "Finished one full scan of IPv4 ranges. Sleeping for 24 hours.")
        time.sleep(86400)


def rescan_unresponsive():
    from . import db_operations
    update_batch = []
    while True:
        down_ips = db_operations.find_down_ips()
        if down_ips:
            for i in db_operations.find_down_ips():
                result = port_scanner.scan_ports(i["_id"])
                now = datetime.now()
                update_data = {
                    "_id": result[0], "ports": result[1], "last_update": now}
                update_batch.append(update_data)
            if update_batch:
                    try:
                        logging.info(f"scanner.py data looks like{update_batch}")
                        db_operations.update_scan_result(update_batch)
                        logging.info(f"Flushed {len(update_batch)} documents to disk")
                        update_batch = []
                    except Exception as e:
                        logging.error(f"ERROR:{e} \ncan not Flushed {len(update_batch)} documents to disk")
                    


            logging.info("Sleeping for 1 hour")
            time.sleep(3600)
        else:
            time.sleep(40)


if __name__ == "__main__":
    db_operations.check_connection()
    t1 = threading.Thread(target=daily_scan, name="DailyScanThread")
    # t2 = threading.Thread(target=rescan_unresponsive,
    #                       name="RescanUnresponsiveThread")

    t1.start()
    # t2.start()
    t1.join()
    # t2.join()

import ipaddress
import logging
import threading
import time
from datetime import datetime

from discovery import db_operations, port_scanner

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
    while True:
        for ip_range in generate_public_ipv4_ranges_stream(24):
            logging.info(f"Scanning: {ip_range}")
            result = port_scanner.call_ip_range(ip_range)
            for ip, ports in result:
                now = datetime.now()
                if db_operations.is_exists(ip):
                    logging.info(f"{ip} is already exists")
                    db_operations.update_scan_result(
                        {"ip": ip, "ports": ports, "last_update": now}
                    )
                else:
                    inserted_id = db_operations.insert_scan_result(
                        {"ip": ip, "ports": ports, "last_update": now}
                    )
                    if inserted_id:
                        logging.info(
                            f"Successfully inserted scan result for {ip} with ID: {inserted_id}"
                        )
        logging.info("Finished one full scan of IPv4 ranges. Sleeping for 24 hours.")
        time.sleep(86400)


def rescan_unresponsive():
    while True:
        down_ips = db_operations.find_down_ips()
        if down_ips:
            for i in db_operations.find_down_ips():
                result = port_scanner.scan_ports(i["ip"])
                now = datetime.now()
                db_operations.update_scan_result(
                    {"ip": result[0], "ports": result[1], "last_update": now}
                )

            logging.info("Sleeping for 1 hour")
            time.sleep(3600)
        else:
            time.sleep(40)


if __name__ == "__main__":
    db_operations.check_connection()
    t1 = threading.Thread(target=daily_scan, name="DailyScanThread")
    t2 = threading.Thread(target=rescan_unresponsive, name="RescanUnresponsiveThread")

    t1.start()
    t2.start()
    t1.join()
    t2.join()

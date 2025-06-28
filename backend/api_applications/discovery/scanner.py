import ipaddress
import logging
import time

import port_scanner
from db_operations import insert_scan_result


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


def main():
    for ip_range in generate_public_ipv4_ranges_stream(24):
        print(f"Scanning: {ip_range}")
        result = port_scanner.call_ip_range(ip_range)
        print(f"this is the result{result}")
        for ip, ports in result:
            inserted_id = insert_scan_result({ip: ports})
            if inserted_id:
                logging.info(
                    f"Successfully inserted scan result for {ip_range} with ID: {inserted_id}"
                )

    print("Finished one full scan of IPv4 ranges. Sleeping for 24 hours.")
    time.sleep(86400)


if __name__ == "__main__":
    main()

import ipaddress

from concurrent.futures import ProcessPoolExecutor, as_completed

import yaml
import os

try:
    from scapy.all import IP, TCP, sr
except KeyboardInterrupt:
    print("\n[!] Import interrupted by user (Scapy took too long to load).")
    import sys

    sys.exit(0)


def scan_ports(ip, ports):
    packets = [IP(dst=ip) / TCP(dport=port, flags="S") for port in ports]
    answers, _ = sr(packets, timeout=5, verbose=0)
    open_ports = []
    for snd, rcv in answers:
        if rcv.haslayer(TCP) and rcv.getlayer(TCP).flags == 0x12:
            open_ports.append(rcv.getlayer(TCP).sport)
    return ip, open_ports


def call_ip_range(ip):
    result = {}
    ips = [str(ip) for ip in ipaddress.ip_network(ip)]
    yaml_path = os.path.join(os.path.dirname(__file__), "ports.yaml")
    with open(yaml_path) as f:
        data = yaml.safe_load(f)
    ports = [item["port"] for item in data["wellknown_ports"]]

    with ProcessPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(scan_ports, ip, ports) for ip in ips]
        for future in as_completed(futures):
            ip, open_ports = future.result()

            if open_ports:
                result[ip] = open_ports
                print(f"{ip}: {open_ports}")
                yield ip, open_ports


def custom_ip(ip, ports=range(1024)):
    result = {}
    open_ports = scan_ports(ip, ports)
    result[open_ports[0]] = open_ports[1]
    return result

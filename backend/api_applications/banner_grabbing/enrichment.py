import socket

import geocoder
import nmap
import requests

scanner = nmap.PortScanner()


def os_finger_print(target, arguments="-O"):
    scanner.scan(target, arguments=arguments)
    if "osmatch" in scanner[target]:
        os_matches = scanner[target]["osmatch"]
        for match in os_matches:
            if "osclass" in match:
                os_class = match["osclass"][0]
                return {
                    "os_match": match["name"],
                    "os_family": os_class["osfamily"],
                    "accuracy": match["accuracy"],
                    "type": os_class["type"],
                    "os_Gen": os_class["osgen"],
                    "vendor": os_class["vendor"],
                }
            else:
                return {"os_match": {match["name"]}, "accuracy": {match["accuracy"]}}


def isp_lookup(ip):
    resp = requests.get(f"http://ip-api.com/json/{ip}").json()
    return {
        "geo": {
            "country": resp["country"],
            "city": resp["city"],
            "regionname": resp["regionName"],
            "latlang": [resp["lat"], resp["lon"]],
        },
        "isp": resp["isp"],
        "organization": resp["org"],
        "asn": resp["as"],
    }


def get_domain(ip):
    try:
        hostname = socket.gethostbyaddr(ip)[0]
        return hostname
    except socket.herror:
        return None

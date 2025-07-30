import requests


def geo_info(ip):
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

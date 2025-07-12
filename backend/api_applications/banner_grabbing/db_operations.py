import logging

from shared_libs import monogo_connections

from . import banner_grabber, enrichment, vulnerability


def update_enrichment():
    try:
        db = monogo_connections.connect_monogo()
        results = list(db.scan_results.find({"finger_print": {"$exists": False}}))

        for i in results:
            logging.info(f"getting OS finger print of : {i}")
            f_p = enrichment.os_finger_print(i["_id"])
            g_l = enrichment.isp_lookup(i["_id"])
            domain = enrichment.get_domain(i["_id"])
            logging.info(
                f"Updating {i['_id']} with f_p={f_p}, g_l={g_l}, domain={domain}"
            )
            db.scan_results.update_one(
                {"_id": i["_id"]},
                {"$set": {"finger_print": f_p, "general": g_l, "domain": domain}},
            )
        return f"{len(results)} updated"
    except Exception as e:
        logging.info(f"Operation do not complete : {e}")
        return None


def update_banners():
    try:
        db = monogo_connections.connect_monogo()
        results = list(db.scan_results.find({"service_type": {"$exists": False}}))
    except Exception as e:
        logging.info(f"Operation do not complete : {e}")
        return None
    for i in results:
        banner = banner_grabber.scan_ports_for_banners(i["_id"], i["ports"])
        logging.info(f"Updating banner, result is: {banner}")
        logging.info(f"getting SERVICE TYPE of : {i}")
        db.scan_results.update_one(
            {"_id": i["_id"]}, {"$set": {"service_type": banner}}
        )

def update_vulnerability():
    try:
        db = monogo_connections.connect_monogo()
        results = list(db.scan_results.find({
        "vulnerability": {"$exists": False},
        "service_type": {"$exists": True, "$ne": None}
    }))
    except Exception as e:
        logging.info(f"Operation do not complete : {e}")
        return None
    for i in results:
        vul = vulnerability.get_vul(i["service_type"])
        logging.info(f"Updating vuls, result is: {vul}")
        logging.info(f"getting vuls of : {i}")
        db.scan_results.update_one(
            {"_id": i["_id"]}, {"$set": {"vulnerability": vul}}
        )

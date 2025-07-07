import logging

from shared_libs import monogo_connections

from banner_grabbing import banner_grabber, enrichment


def update_enrichment():
    try:
        db = monogo_connections.connect_monogo()
        results = list(db.scan_results.find({"finger_print": {"$exists": False}}))

        for i in results:
            logging.info(f"getting OS finger print of : {i}")
            f_p = enrichment.os_finger_print(i["ip"])
            g_l = enrichment.isp_lookup(i["ip"])
            domain = enrichment.get_domain(i["ip"])
            logging.info(
                f"Updating {i['ip']} with f_p={f_p}, g_l={g_l}, domain={domain}"
            )
            db.scan_results.update_one(
                {"ip": i["ip"]},
                {"$set": {"finger_print": f_p, "general": g_l, "domain": domain}},
            )
        return f"{len(results)} updated"
    except Exception as e:
        logging.info(f"Operation do not complete : {e}")
        return None


def update_banners():
    try:
        db = monogo_connections.connect_monogo()
        results = list(db.scan_results.find({"banners": {"$exists": False}}))
    except Exception as e:
        logging.info(f"Operation do not complete : {e}")
        return None
    for i in results:
        banner = banner_grabber.scan_ports_for_banners(i["ip"], i["ports"])
        logging.info(f"getting SERVICE TYPE of : {i}")
        db.scan_results.update_one({"ip": i["ip"]}, {"$set": {"service_type": banner}})

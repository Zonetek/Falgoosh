import logging

from shared_libs import monogo_connections

from . import dns_reverse, finger_print, geo_info



def update_enrichment():

    try:
        db = monogo_connections.connect_monogo()
        results = list(
            db.scan_results.find(
                {
                    "finger_print": {"$exists": False}
                }
            )
        )

        for i in results:

            try:

                logging.info(f"getting OS finger print of : {i}")

                f_p = finger_print.os_finger_print(i["_id"])
                g_l = geo_info.geo_info(i["_id"])
                domain = dns_reverse.get_domain(i["_id"])

                logging.info(
                    f"Updating {i['_id']} with f_p={f_p}, g_l={g_l}, domain={domain}"
                )

                db.scan_results.update_one(
                    {"_id": i["_id"]},
                    {"$set": {"finger_print": f_p, "general": g_l, "domain": domain}},
                )

            except Exception as e:
                logging.error(f"Failed enrichment for {i['_id']}: {e}", exc_info=True)

    except Exception as e:
        logging.error(f"Operation do not complete in enrichs : {e}")

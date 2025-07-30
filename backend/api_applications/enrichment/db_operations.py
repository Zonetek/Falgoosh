import logging

from shared_libs import monogo_connections

from . import dns_reverse, finger_print, geo_info
from shared_models import schema


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
                finger_print_model = schema.FingerPrintInfo(**f_p)
                general_model = schema.GeneralInfo(**g_l)
                update_fields = {}
                if finger_print_model:
                    update_fields["finger_print"] = finger_print_model.dict()
                if general_model:
                    update_fields["general"] = general_model.dict()
                if domain:
                    update_fields["domain"] = domain
                logging.info(
                    f"Updating {i['_id']} with f_p={f_p}, g_l={g_l}, domain={domain}"
                )
                db.scan_results.update_one(
                    {"_id": i["_id"]},
                    {"$set": update_fields},
                )
            except Exception as e:
                logging.error(f"Failed enrichment for {i['_id']}: {e}", exc_info=True)
    except Exception as e:
        logging.error(f"Operation do not complete in enrichs : {e}")
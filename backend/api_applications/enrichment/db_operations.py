import logging
from pymongo import UpdateOne

from shared_libs import monogo_connections

from . import dns_reverse, finger_print, geo_info
from shared_models import schema


def update_enrichment(results):

    try:

        db = monogo_connections.connect_monogo()
        operations = []

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
                # db.scan_results.update_one(
                #     {"_id": i["_id"]},
                #     {"$set": update_fields},
                # )
                operations.append(
                    UpdateOne(
                        {"_id": i["_id"]},
                        {
                            "$set": update_fields
                                
                        },
                        upsert=True,
                    )
                )
            except Exception as e:
                logging.error(
                    f"Failed enrichment for {i['_id']}: {e}", exc_info=True)

        if operations:
            result = db.scan_results.bulk_write(operations, ordered=False)
            logging.info(f"Flushed {operations}\n updates in one batch to db")

    except Exception as e:
        logging.error(f"Operation do not complete in enrichs : {e}")

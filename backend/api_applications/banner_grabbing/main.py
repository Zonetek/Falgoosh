import logging
import threading
import schedule
from . import db_operations,vulnerability

import os
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def main():
    while True:
        db_operations.update_enrichment()
        db_operations.update_banners()
        db_operations.update_vulnerability()
        enrichment_thread = threading.Thread(
            target=db_operations.update_enrichment, name="EnrichmentThread"
        )
        banners_thread = threading.Thread(
            target=db_operations.update_banners, name="BannersThread"
        )
        vulnerability_thread = threading.Thread(
            target=db_operations.update_vulnerability, name="VulnerabilityThread"
        )
        enrichment_thread.start()
        banners_thread.start()
        vulnerability_thread.start()
        logging.info("Waiting for enrichment and banner threads to complete...")
        enrichment_thread.join()
        banners_thread.join()
        vulnerability_thread.join()
        schedule.every(1.5).hours.do(vulnerability.download_and_replace_nvd, os.path.join(os.path.dirname(__file__), "cve_data"))


if __name__ == "__main__":
    main()

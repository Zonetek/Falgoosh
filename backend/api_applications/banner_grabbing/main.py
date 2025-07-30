import logging
import os
import threading

import schedule

from . import db_operations, vulnerability

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def main():
    while True:
        banners_thread = threading.Thread(
            target=db_operations.update_banners, name="BannersThread"
        )
        vulnerability_thread = threading.Thread(
            target=db_operations.update_vulnerability, name="VulnerabilityThread"
        )
        banners_thread.start()
        vulnerability_thread.start()
        logging.info("Waiting for enrichment and banner threads to complete...")
        banners_thread.join()
        vulnerability_thread.join()
        try:
            schedule.every(1.5).hours.do(
                vulnerability.download_and_replace_nvd,
                os.path.join(os.path.dirname(__file__), "cve_data"),
            )
        
        except Exception as e:
            logging.error("Failed to download and replace CVE file.")
            
            


if __name__ == "__main__":
    main()

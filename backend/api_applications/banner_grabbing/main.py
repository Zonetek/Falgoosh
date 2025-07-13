import logging
import threading

from banner_grabbing import db_operations

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def main():
    while True:
        db_operations.update_enrichment()
        db_operations.update_banners()
        enrichment_thread = threading.Thread(
            target=db_operations.update_enrichment, name="EnrichmentThread"
        )
        banners_thread = threading.Thread(
            target=db_operations.update_banners, name="BannersThread"
        )
        enrichment_thread.start()
        banners_thread.start()
        logging.info("Waiting for enrichment and banner threads to complete...")
        enrichment_thread.join()
        banners_thread.join()


if __name__ == "__main__":
    main()

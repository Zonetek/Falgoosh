import logging

from banner_grabbing import db_operations, finger_print

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def main():
    while True:
        logging.info(f"what is returend {db_operations.update_results()}")


if __name__ == "__main__":
    main()

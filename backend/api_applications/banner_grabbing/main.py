import logging

from . import banner_counsumer

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def main():
    while True:
        banner_counsumer.get_batches()
        # db_operations.update_banners()
            


if __name__ == "__main__":
    main()

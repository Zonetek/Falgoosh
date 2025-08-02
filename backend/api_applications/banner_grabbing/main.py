import logging

from . import db_operations

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def main():
    while True:
        db_operations.update_banners()
            


if __name__ == "__main__":
    main()

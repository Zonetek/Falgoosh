from . import db_operations


def main():

    while(True):
        db_operations.update_enrichment()

    
if __name__ == "__main__":
    main()

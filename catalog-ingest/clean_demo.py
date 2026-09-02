from catalog_ingest.config import get_settings
from catalog_ingest.db import session_scope
from catalog_ingest.models import Product

def main():
    settings = get_settings()
    with session_scope(settings) as session:
        count = session.query(Product).filter(Product.source == 'demo').delete()
        print(f"Deleted {count} demo products")

if __name__ == "__main__":
    main()

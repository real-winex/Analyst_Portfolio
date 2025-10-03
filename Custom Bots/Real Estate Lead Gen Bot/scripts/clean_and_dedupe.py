from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Property, Owner
from utils.cleaner import clean_address, clean_owner_name
from utils.deduper import deduplicate_leads
import os
from dotenv import load_dotenv

def main():
    load_dotenv()
    database_url = os.getenv('DATABASE_URL', 'sqlite:///data/properties.db')
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        # Clean addresses and owner names
        print("Cleaning addresses and owner names...")
        properties = session.query(Property).all()
        for prop in properties:
            cleaned_address = clean_address(prop.address)
            if cleaned_address != prop.address:
                print(f"Updating address: {prop.address} -> {cleaned_address}")
                prop.address = cleaned_address
            if prop.owner:
                cleaned_owner = clean_owner_name(prop.owner.name)
                if cleaned_owner != prop.owner.name:
                    print(f"Updating owner: {prop.owner.name} -> {cleaned_owner}")
                    prop.owner.name = cleaned_owner
        session.commit()
        print("Cleaning complete.")
        # Deduplicate
        print("Deduplicating leads...")
        deduplicate_leads(session)
        print("Deduplication complete.")
    finally:
        session.close()

if __name__ == "__main__":
    main() 
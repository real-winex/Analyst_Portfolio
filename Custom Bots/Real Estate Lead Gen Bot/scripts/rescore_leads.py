from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Property
from utils.scorer import rescore_all_properties
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
        print("Rescoring all leads...")
        rescore_all_properties(session)
        print("Rescoring complete.")
    finally:
        session.close()

if __name__ == "__main__":
    main()
 
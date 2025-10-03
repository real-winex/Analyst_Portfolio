from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from scrapers.facebook import FacebookScraper
from models import Base
import os
from dotenv import load_dotenv

def main():
    # Load environment variables
    load_dotenv()
    
    # Verify Facebook credentials
    if not os.getenv('FACEBOOK_EMAIL') or not os.getenv('FACEBOOK_PASSWORD'):
        print("Error: Facebook credentials not found in .env file")
        print("Please add FACEBOOK_EMAIL and FACEBOOK_PASSWORD to your .env file")
        return
    
    # Create database engine and session
    database_url = os.getenv('DATABASE_URL', 'sqlite:///data/properties.db')
    engine = create_engine(database_url)
    
    # Create tables if they don't exist
    Base.metadata.create_all(engine)
    
    # Create database session
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Load proxy list if available
        proxy_list = None
        if os.getenv('PROXY_LIST'):
            proxy_list = os.getenv('PROXY_LIST').split(',')
        
        # Initialize scraper
        scraper = FacebookScraper(
            session,
            use_proxies=bool(proxy_list),
            proxy_list=proxy_list
        )
        
        # Example: Search for properties in multiple zipcodes
        zipcodes = [
            "90210",  # Beverly Hills
            "90077",  # Bel Air
            "90069",  # West Hollywood
            # Add more zipcodes as needed
        ]
        
        total_properties = 0
        for zipcode in zipcodes:
            print(f"\nSearching for properties in zipcode: {zipcode}")
            
            # Get properties (limit to 50 per zipcode to avoid too many requests)
            properties = scraper.search_by_zipcode(zipcode, max_listings=50)
            print(f"Found {len(properties)} properties in {zipcode}")
            
            # Save to database
            scraper.save_properties(properties)
            total_properties += len(properties)
            
            # Print some stats
            for prop in properties:
                print(f"\nProperty at {prop['address']}")
                print(f"Price: ${prop['price']:,.2f}")
                print(f"Details: {prop.get('bedrooms', 'N/A')} beds, "
                      f"{prop.get('bathrooms', 'N/A')} baths, "
                      f"{prop.get('square_feet', 'N/A')} sqft")
                if prop.get('owner_name'):
                    print(f"Seller: {prop['owner_name']}")
                if prop.get('distress_indicators'):
                    print(f"Distress indicators: {', '.join(prop['distress_indicators'])}")
        
        print(f"\nTotal properties found across all zipcodes: {total_properties}")
    
    except Exception as e:
        print(f"Error: {str(e)}")
    
    finally:
        session.close()

if __name__ == "__main__":
    main() 
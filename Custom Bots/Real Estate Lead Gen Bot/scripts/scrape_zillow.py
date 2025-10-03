from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from scrapers.zillow import ZillowScraper
from models import Base
import os
from dotenv import load_dotenv

def load_proxy_list() -> list:
    """Load proxies from file or environment variable."""
    # Try loading from environment variable first
    proxy_list = os.getenv('PROXY_LIST')
    if proxy_list:
        return proxy_list.split(',')
    
    # Try loading from file
    proxy_file = os.getenv('PROXY_FILE', 'proxies.txt')
    if os.path.exists(proxy_file):
        with open(proxy_file, 'r') as f:
            return [line.strip() for line in f if line.strip()]
    
    return []

def main():
    # Load environment variables
    load_dotenv()
    
    # Create database engine and session
    database_url = os.getenv('DATABASE_URL', 'sqlite:///data/properties.db')
    engine = create_engine(database_url)
    
    # Create tables if they don't exist
    Base.metadata.create_all(engine)
    
    # Create database session
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Load proxy list
        proxy_list = load_proxy_list()
        use_proxies = bool(proxy_list or os.getenv('WEBSHARE_API_KEY') or os.getenv('PROXYSCRAPE_API_KEY'))
        
        # Initialize scraper with proxy support
        scraper = ZillowScraper(
            session,
            use_proxies=use_proxies,
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
            print(f"\nSearching for FSBO properties in zipcode: {zipcode}")
            
            # Get properties
            properties = scraper.search_by_zipcode(zipcode)
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
                if prop.get('distress_indicators'):
                    print(f"Distress indicators: {', '.join(prop['distress_indicators'])}")
        
        print(f"\nTotal properties found across all zipcodes: {total_properties}")
    
    except Exception as e:
        print(f"Error: {str(e)}")
    
    finally:
        session.close()

if __name__ == "__main__":
    main() 
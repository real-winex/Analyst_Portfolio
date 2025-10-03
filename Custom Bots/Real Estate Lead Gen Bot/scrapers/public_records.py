import os
import requests
import pandas as pd
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from datetime import datetime
from models import Property, Owner
from sqlalchemy.orm import Session
import logging

class PublicRecordsScraper:
    def __init__(self, session: Session):
        """
        Initialize the public records scraper.
        Args:
            session: SQLAlchemy session for database operations
        """
        self.session = session
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            filename='public_records_scraper.log'
        )
        self.logger = logging.getLogger(__name__)

    def scrape_html_table(self, url: str, address_col: str, owner_col: str, distress_type: str, max_rows: int = 100) -> List[Dict]:
        """
        Scrape a public records HTML table from a given URL.
        Args:
            url: The URL of the public records page
            address_col: The column name for property address
            owner_col: The column name for owner name
            distress_type: The type of distress (e.g., 'probate', 'foreclosure')
            max_rows: Maximum number of rows to process
        Returns:
            List of property dictionaries
        """
        properties = []
        try:
            response = requests.get(url)
            if response.status_code != 200:
                self.logger.error(f"Failed to fetch {url} (status {response.status_code})")
                return properties
            soup = BeautifulSoup(response.text, 'html.parser')
            table = soup.find('table')
            if not table:
                self.logger.error(f"No table found at {url}")
                return properties
            df = pd.read_html(str(table))[0]
            for _, row in df.head(max_rows).iterrows():
                address = row.get(address_col)
                owner = row.get(owner_col)
                if not address:
                    continue
                properties.append({
                    'address': address,
                    'owner_name': owner,
                    'distress_type': distress_type
                })
        except Exception as e:
            self.logger.error(f"Error scraping HTML table: {str(e)}")
        return properties

    def scrape_csv(self, url: str, address_col: str, owner_col: str, distress_type: str, max_rows: int = 100) -> List[Dict]:
        """
        Download and parse a CSV file from a public records site.
        Args:
            url: The URL of the CSV file
            address_col: The column name for property address
            owner_col: The column name for owner name
            distress_type: The type of distress (e.g., 'tax_delinquent')
            max_rows: Maximum number of rows to process
        Returns:
            List of property dictionaries
        """
        properties = []
        try:
            df = pd.read_csv(url)
            for _, row in df.head(max_rows).iterrows():
                address = row.get(address_col)
                owner = row.get(owner_col)
                if not address:
                    continue
                properties.append({
                    'address': address,
                    'owner_name': owner,
                    'distress_type': distress_type
                })
        except Exception as e:
            self.logger.error(f"Error scraping CSV: {str(e)}")
        return properties

    def save_properties(self, properties: List[Dict]) -> None:
        """Save scraped properties to database."""
        saved_count = 0
        error_count = 0
        for prop_data in properties:
            try:
                # Create owner record
                owner = None
                if prop_data.get('owner_name'):
                    owner = Owner(
                        name=prop_data.get('owner_name'),
                        phone=None,
                        email=None
                    )
                    self.session.add(owner)
                    self.session.flush()
                # Create property record
                property = Property(
                    address=prop_data['address'],
                    price=None,
                    bedrooms=None,
                    bathrooms=None,
                    square_feet=None,
                    property_type='unknown',
                    listing_date=datetime.now(),
                    source='public_records',
                    source_url=prop_data.get('source_url', ''),
                    owner_id=owner.id if owner else None,
                    distress_score=80,  # Public records are strong distress indicators
                )
                self.session.add(property)
                saved_count += 1
                if saved_count % 10 == 0:
                    self.session.commit()
            except Exception as e:
                self.logger.error(f"Error saving property: {str(e)}")
                error_count += 1
                continue
        try:
            self.session.commit()
        except Exception as e:
            self.logger.error(f"Error in final commit: {str(e)}")
            self.session.rollback()
        self.logger.info(f"Saved {saved_count} properties with {error_count} errors") 
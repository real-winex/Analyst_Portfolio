import time
import random
from typing import List, Dict, Optional
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from models import Property, Owner
from sqlalchemy.orm import Session
from config.settings import DISTRESS_KEYWORDS
import logging
import json
import os
from utils.proxy_manager import ProxyManager

class FacebookScraper:
    def __init__(self, session: Session, use_proxies: bool = False, proxy_list: List[str] = None):
        """
        Initialize the Facebook Marketplace scraper
        
        Args:
            session: SQLAlchemy session for database operations
            use_proxies: Whether to use proxy rotation
            proxy_list: Optional list of proxy URLs to use
        """
        self.session = session
        self.use_proxies = use_proxies
        self.proxy_manager = ProxyManager(proxy_list) if use_proxies else None
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            filename='facebook_scraper.log'
        )
        self.logger = logging.getLogger(__name__)
        
        # Initialize webdriver
        self.driver = None
        self.wait = None
        self.setup_driver()
        
        # Facebook credentials
        self.fb_email = os.getenv('FACEBOOK_EMAIL')
        self.fb_password = os.getenv('FACEBOOK_PASSWORD')
        
        if not self.fb_email or not self.fb_password:
            raise ValueError("Facebook credentials not found in environment variables")
            
        # Base URLs
        self.base_url = "https://www.facebook.com"
        self.marketplace_url = f"{self.base_url}/marketplace"
        
        # Delay settings
        self.min_delay = 2
        self.max_delay = 5

    def setup_driver(self):
        """Configure and initialize Chrome WebDriver with appropriate options."""
        chrome_options = Options()
        
        # Add proxy if enabled
        if self.use_proxies and self.proxy_manager:
            proxy = self.proxy_manager.get_proxy()
            if proxy:
                chrome_options.add_argument(f'--proxy-server={proxy["http"]}')
        
        # Add other Chrome options
        chrome_options.add_argument('--disable-notifications')
        chrome_options.add_argument('--disable-infobars')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--lang=en-US')
        
        # Add user agent
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Initialize the driver
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)
        
        # Set window size
        self.driver.set_window_size(1920, 1080)

    def login(self) -> bool:
        """Log into Facebook account."""
        try:
            self.logger.info("Attempting to log in to Facebook...")
            self.driver.get(self.base_url)
            
            # Wait for and fill in email
            email_field = self.wait.until(
                EC.presence_of_element_located((By.ID, "email"))
            )
            email_field.send_keys(self.fb_email)
            
            # Fill in password
            password_field = self.driver.find_element(By.ID, "pass")
            password_field.send_keys(self.fb_password)
            
            # Click login button
            login_button = self.driver.find_element(
                By.CSS_SELECTOR, 
                "[data-testid='royal_login_button']"
            )
            login_button.click()
            
            # Wait for login to complete
            time.sleep(5)  # Give time for login to process
            
            # Check if login was successful
            try:
                self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[aria-label='Marketplace']"))
                )
                self.logger.info("Successfully logged in to Facebook")
                return True
            except TimeoutException:
                self.logger.error("Failed to verify login success")
                return False
                
        except Exception as e:
            self.logger.error(f"Login failed: {str(e)}")
            return False

    def search_by_zipcode(self, zipcode: str, max_listings: int = 100) -> List[Dict]:
        """
        Search for FSBO properties in Facebook Marketplace by zipcode.
        
        Args:
            zipcode: The zipcode to search in
            max_listings: Maximum number of listings to scrape
            
        Returns:
            List of property dictionaries
        """
        properties = []
        
        try:
            # Ensure logged in
            if not self.login():
                self.logger.error("Could not log in to Facebook")
                return properties
            
            # Navigate to Marketplace
            self.driver.get(f"{self.marketplace_url}/category/propertyrentals")
            time.sleep(random.uniform(2, 4))
            
            # Set location to zipcode
            try:
                # Click location button
                location_button = self.wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "[aria-label='Change location']"))
                )
                location_button.click()
                
                # Input zipcode
                location_input = self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder='Search by location']"))
                )
                location_input.clear()
                location_input.send_keys(zipcode)
                
                # Wait for and click the first suggestion
                time.sleep(2)
                suggestion = self.wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "[role='option']"))
                )
                suggestion.click()
                
            except Exception as e:
                self.logger.error(f"Error setting location: {str(e)}")
                return properties
            
            # Add filters for FSBO/owner properties
            try:
                # Click filters button
                filter_button = self.wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "[aria-label='Filters']"))
                )
                filter_button.click()
                
                # Set filters (implementation depends on Facebook's current filter UI)
                # You might need to adjust these selectors based on the actual UI
                
            except Exception as e:
                self.logger.error(f"Error setting filters: {str(e)}")
            
            # Scroll and collect listings
            listings_processed = 0
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            
            while listings_processed < max_listings:
                # Find all listing cards
                listing_cards = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    "div[role='main'] > div > div > div > div > div > div[style]"
                )
                
                for card in listing_cards[listings_processed:]:
                    try:
                        # Extract basic info from card
                        title = card.find_element(By.CSS_SELECTOR, "span").text
                        price = card.find_element(By.CSS_SELECTOR, "span[style]").text
                        
                        # Click to open listing details
                        card.click()
                        time.sleep(random.uniform(1, 2))
                        
                        # Extract detailed information
                        property_details = self._extract_property_details()
                        
                        if property_details:
                            properties.append(property_details)
                            listings_processed += 1
                            
                            if listings_processed >= max_listings:
                                break
                        
                        # Close listing details
                        close_button = self.wait.until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, "[aria-label='Close']"))
                        )
                        close_button.click()
                        time.sleep(random.uniform(1, 2))
                        
                    except Exception as e:
                        self.logger.error(f"Error processing listing: {str(e)}")
                        continue
                
                # Scroll down
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(random.uniform(2, 3))
                
                # Check if we've reached the bottom
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
            
        except Exception as e:
            self.logger.error(f"Error during search: {str(e)}")
            
        finally:
            self.cleanup()
            
        return properties

    def _extract_property_details(self) -> Optional[Dict]:
        """Extract property details from the listing modal."""
        try:
            details = {}
            
            # Wait for modal to load
            self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='dialog']"))
            )
            
            # Extract price
            price_elem = self.driver.find_element(
                By.CSS_SELECTOR,
                "div[role='dialog'] span[style]"
            )
            details['price'] = float(price_elem.text.replace('$', '').replace(',', ''))
            
            # Extract description
            description_elem = self.driver.find_element(
                By.CSS_SELECTOR,
                "div[role='dialog'] div[style] > span"
            )
            details['description'] = description_elem.text
            
            # Check for distress indicators in description
            details['distress_indicators'] = [
                keyword for keyword in DISTRESS_KEYWORDS
                if keyword.lower() in details['description'].lower()
            ]
            
            # Extract location
            location_elem = self.driver.find_element(
                By.CSS_SELECTOR,
                "div[role='dialog'] div[style] > span[style]"
            )
            details['address'] = location_elem.text
            
            # Try to extract additional details from description
            desc_lower = details['description'].lower()
            
            # Look for bedrooms
            if 'bed' in desc_lower:
                bed_idx = desc_lower.find('bed')
                possible_number = desc_lower[max(0, bed_idx-10):bed_idx].strip()
                try:
                    details['bedrooms'] = int(''.join(filter(str.isdigit, possible_number)))
                except:
                    pass
            
            # Look for bathrooms
            if 'bath' in desc_lower:
                bath_idx = desc_lower.find('bath')
                possible_number = desc_lower[max(0, bath_idx-10):bath_idx].strip()
                try:
                    details['bathrooms'] = float(''.join(filter(lambda x: x.isdigit() or x == '.', possible_number)))
                except:
                    pass
            
            # Look for square footage
            if 'sqft' in desc_lower or 'sq ft' in desc_lower or 'square feet' in desc_lower:
                for term in ['sqft', 'sq ft', 'square feet']:
                    if term in desc_lower:
                        idx = desc_lower.find(term)
                        possible_number = desc_lower[max(0, idx-10):idx].strip()
                        try:
                            details['square_feet'] = int(''.join(filter(str.isdigit, possible_number)))
                            break
                        except:
                            pass
            
            # Get seller information
            try:
                seller_name = self.driver.find_element(
                    By.CSS_SELECTOR,
                    "div[role='dialog'] h2"
                ).text
                details['owner_name'] = seller_name
            except:
                pass
            
            return details
            
        except Exception as e:
            self.logger.error(f"Error extracting property details: {str(e)}")
            return None

    def save_properties(self, properties: List[Dict]) -> None:
        """Save scraped properties to database."""
        saved_count = 0
        error_count = 0
        
        for prop_data in properties:
            try:
                # Create owner record if contact info exists
                owner = None
                if prop_data.get('owner_name'):
                    owner = Owner(
                        name=prop_data.get('owner_name'),
                        phone=prop_data.get('owner_phone'),
                        email=prop_data.get('owner_email')
                    )
                    self.session.add(owner)
                    self.session.flush()
                
                # Calculate distress score
                distress_score = len(prop_data.get('distress_indicators', [])) * 10
                
                # Create property record
                property = Property(
                    address=prop_data['address'],
                    price=prop_data['price'],
                    bedrooms=prop_data.get('bedrooms'),
                    bathrooms=prop_data.get('bathrooms'),
                    square_feet=prop_data.get('square_feet'),
                    property_type='single_family',
                    listing_date=datetime.now(),
                    source='facebook',
                    source_url=prop_data.get('source_url', ''),
                    owner_id=owner.id if owner else None,
                    distress_score=distress_score
                )
                
                self.session.add(property)
                saved_count += 1
                
                # Commit every 10 properties
                if saved_count % 10 == 0:
                    self.session.commit()
                
            except Exception as e:
                self.logger.error(f"Error saving property: {str(e)}")
                error_count += 1
                continue
        
        # Final commit
        try:
            self.session.commit()
        except Exception as e:
            self.logger.error(f"Error in final commit: {str(e)}")
            self.session.rollback()
            
        self.logger.info(f"Saved {saved_count} properties with {error_count} errors")

    def cleanup(self):
        """Clean up resources."""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass

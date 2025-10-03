import time
import random
import json
from typing import List, Dict, Optional
from datetime import datetime
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import requests
from requests.exceptions import RequestException
from models import Property, Owner
from sqlalchemy.orm import Session
from config.settings import DISTRESS_KEYWORDS
import logging
from utils.proxy_manager import ProxyManager

class ZillowScraper:
    def __init__(self, session: Session, use_proxies: bool = False, proxy_list: List[str] = None):
        """
        Initialize the Zillow scraper
        
        Args:
            session: SQLAlchemy session for database operations
            use_proxies: Whether to use proxy rotation (recommended for production)
            proxy_list: Optional list of proxy URLs to use
        """
        self.session = session
        self.use_proxies = use_proxies
        self.ua = UserAgent()
        self.base_url = "https://www.zillow.com"
        self.search_url = f"{self.base_url}/fsbo"
        
        # Reduced delays since we're running less frequently
        # Still random but faster (0.5-2 seconds)
        self.min_delay = 0.5
        self.max_delay = 2
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            filename='zillow_scraper.log'
        )
        self.logger = logging.getLogger(__name__)
        
        # Track requests to avoid overloading
        self.request_count = 0
        self.max_requests_per_session = 500  # Increased since we run weekly
        self.session_start_time = datetime.now()
        
        # Initialize proxy manager if using proxies
        self.proxy_manager = ProxyManager(proxy_list) if use_proxies else None

    def _get_headers(self) -> Dict[str, str]:
        """Generate random headers for each request."""
        return {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            # Add more browser-like headers
            'Cache-Control': 'max-age=0',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'DNT': '1'  # Do Not Track
        }

    def _get_proxy(self) -> Optional[Dict[str, str]]:
        """Get a proxy from the proxy manager."""
        if not self.use_proxies or not self.proxy_manager:
            return None
        return self.proxy_manager.get_proxy()

    def _should_pause(self) -> bool:
        """Check if we should pause scraping to avoid detection."""
        self.request_count += 1
        
        # If we've made too many requests, pause
        if self.request_count >= self.max_requests_per_session:
            self.logger.warning("Reached maximum requests for session, pausing...")
            time.sleep(300)  # 5-minute cooldown
            self.request_count = 0
            self.session_start_time = datetime.now()
            return True
            
        # If we're going too fast, add extra delay
        if self.request_count % 50 == 0:
            self.logger.info("Adding extra delay every 50 requests...")
            time.sleep(random.uniform(5, 10))
            
        return False

    def _extract_price(self, price_text: str) -> float:
        """Extract numeric price from string."""
        try:
            return float(price_text.replace('$', '').replace(',', ''))
        except (ValueError, AttributeError):
            return 0.0

    def _extract_property_details(self, soup: BeautifulSoup) -> Dict:
        """Extract property details from the listing page."""
        details = {}
        
        try:
            # Basic info
            price_elem = soup.find('span', {'data-testid': 'price'})
            if not price_elem:
                # Try alternative price selectors
                price_elem = soup.find('span', {'class': 'price'}) or \
                           soup.find('div', {'class': 'price'}) or \
                           soup.find('span', string=lambda x: x and '$' in x)
            
            details['price'] = self._extract_price(price_elem.text if price_elem else '0')

            # Extract address components - try multiple selectors
            address_div = soup.find('div', {'class': 'property-address'}) or \
                         soup.find('h1', {'class': 'address'}) or \
                         soup.find('div', {'class': 'address'})
            if address_div:
                details['address'] = address_div.text.strip()
            
            # Extract property facts - try multiple selectors
            facts_div = soup.find('div', {'class': 'home-facts-at-a-glance'}) or \
                       soup.find('div', {'class': 'property-facts'}) or \
                       soup.find('div', {'class': 'facts-at-a-glance'})
            
            if facts_div:
                # Try multiple patterns for each fact
                for bed_pattern in ['bed', 'bedroom', 'beds']:
                    beds = facts_div.find(string=lambda x: bed_pattern in str(x).lower())
                    if beds:
                        details['bedrooms'] = int(''.join(filter(str.isdigit, beds)))
                        break
                
                for bath_pattern in ['bath', 'bathroom', 'baths']:
                    baths = facts_div.find(string=lambda x: bath_pattern in str(x).lower())
                    if baths:
                        details['bathrooms'] = float(''.join(filter(lambda x: x.isdigit() or x == '.', baths)))
                        break
                
                for sqft_pattern in ['sqft', 'sq ft', 'square feet', 'square foot']:
                    sqft = facts_div.find(string=lambda x: sqft_pattern in str(x).lower())
                    if sqft:
                        details['square_feet'] = int(''.join(filter(str.isdigit, sqft)))
                        break

            # Extract description and look for distress indicators
            description_div = soup.find('div', {'class': 'property-description'}) or \
                            soup.find('div', {'class': 'description'}) or \
                            soup.find('div', {'class': 'remarks'})
            
            if description_div:
                details['description'] = description_div.text.strip()
                
                # Check for distress indicators in description
                details['distress_indicators'] = [
                    keyword for keyword in DISTRESS_KEYWORDS 
                    if keyword.lower() in details['description'].lower()
                ]
                
                # Additional distress indicators
                if any(urgent_word in details['description'].lower() 
                      for urgent_word in ['urgent', 'immediate', 'quick sale', 'must sell']):
                    details['distress_indicators'].append('urgent_sale')
                    
                if any(repair_word in details['description'].lower()
                      for repair_word in ['needs work', 'fixer', 'as-is', 'repair']):
                    details['distress_indicators'].append('needs_repair')

            # Try to extract days on market
            dom_elem = soup.find(string=lambda x: 'days on' in str(x).lower())
            if dom_elem:
                try:
                    details['days_on_market'] = int(''.join(filter(str.isdigit, dom_elem)))
                except ValueError:
                    pass

        except Exception as e:
            self.logger.error(f"Error extracting property details: {str(e)}")
            
        return details

    def _make_request(self, url: str, params: Dict = None) -> Optional[requests.Response]:
        """Make a request with proxy support and failure handling."""
        max_retries = 3
        current_try = 0
        
        while current_try < max_retries:
            try:
                headers = self._get_headers()
                proxy = self._get_proxy() if self.use_proxies else None
                
                response = requests.get(
                    url,
                    params=params,
                    headers=headers,
                    proxies=proxy,
                    timeout=30
                )
                
                if response.status_code == 200:
                    if proxy:
                        self.proxy_manager.report_success(proxy)
                    return response
                    
                elif response.status_code in [403, 429]:  # Forbidden or Too Many Requests
                    if proxy:
                        self.proxy_manager.report_failure(proxy)
                    self.logger.warning(f"Rate limited or blocked. Status: {response.status_code}")
                    time.sleep(random.uniform(5, 10))  # Longer delay on rate limit
                    
                else:
                    if proxy:
                        self.proxy_manager.report_failure(proxy)
                    self.logger.warning(f"Unexpected status code: {response.status_code}")
                
            except RequestException as e:
                if proxy:
                    self.proxy_manager.report_failure(proxy)
                self.logger.error(f"Request failed: {str(e)}")
                
            current_try += 1
            if current_try < max_retries:
                time.sleep(random.uniform(2, 5))  # Delay between retries
                
        return None

    def search_by_zipcode(self, zipcode: str, max_pages: int = 20) -> List[Dict]:
        """
        Search for FSBO properties in a specific zipcode.
        
        Args:
            zipcode: The zipcode to search in
            max_pages: Maximum number of pages to scrape (default 20)
            
        Returns:
            List of property dictionaries
        """
        properties = []
        page = 1
        
        self.logger.info(f"Starting search for zipcode {zipcode}")
        
        while page <= max_pages:
            try:
                if self._should_pause():
                    continue
                
                time.sleep(random.uniform(self.min_delay, self.max_delay))
                
                # Construct search URL with filters
                search_params = {
                    'searchQueryState': json.dumps({
                        'pagination': {'currentPage': page},
                        'usersSearchTerm': zipcode,
                        'filterState': {
                            'fsba': {'value': False},
                            'fsbo': {'value': True},
                            'sort': {'value': 'days'},
                            'price': {'min': 0},  # Include all price ranges
                            'doz': {'value': '90'},  # Last 90 days
                        }
                    })
                }
                
                response = self._make_request(self.search_url, search_params)
                if not response:
                    self.logger.warning(f"Failed to get search page {page} after retries")
                    break
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find all property cards - try multiple selectors
                property_cards = soup.find_all('article', {'class': 'property-card'}) or \
                               soup.find_all('div', {'class': 'list-card'}) or \
                               soup.find_all('li', {'class': 'listing-card'})
                
                if not property_cards:
                    self.logger.info(f"No more properties found on page {page}")
                    break
                    
                self.logger.info(f"Found {len(property_cards)} properties on page {page}")
                
                for card in property_cards:
                    try:
                        # Get property link - try multiple selectors
                        link = card.find('a', {'class': 'property-card-link'}) or \
                               card.find('a', {'class': 'list-card-link'}) or \
                               card.find('a', href=True)
                               
                        if not link:
                            continue
                            
                        property_url = f"{self.base_url}{link['href']}" if link['href'].startswith('/') else link['href']
                        
                        if self._should_pause():
                            continue
                            
                        time.sleep(random.uniform(self.min_delay, self.max_delay))
                        
                        property_response = self._make_request(property_url)
                        if not property_response:
                            continue
                            
                        property_soup = BeautifulSoup(property_response.text, 'html.parser')
                        property_details = self._extract_property_details(property_soup)
                        
                        property_details.update({
                            'source': 'zillow',
                            'source_url': property_url,
                            'listing_date': datetime.now(),
                            'zipcode': zipcode
                        })
                        
                        properties.append(property_details)
                        self.logger.info(f"Successfully processed property: {property_url}")
                        
                    except Exception as e:
                        self.logger.error(f"Error processing property: {str(e)}")
                        continue
                
                page += 1
                
            except Exception as e:
                self.logger.error(f"Error during search: {str(e)}")
                break
                
        self.logger.info(f"Completed search for zipcode {zipcode}. Found {len(properties)} properties.")
        return properties

    def save_properties(self, properties: List[Dict]) -> None:
        """Save scraped properties to database."""
        saved_count = 0
        error_count = 0
        
        for prop_data in properties:
            try:
                # Check if property already exists
                existing_property = self.session.query(Property).filter_by(
                    source_url=prop_data['source_url']
                ).first()
                
                if existing_property:
                    # Update existing property
                    for key, value in prop_data.items():
                        if hasattr(existing_property, key):
                            setattr(existing_property, key, value)
                    self.logger.info(f"Updated existing property: {prop_data['address']}")
                else:
                    # Create owner record if contact info exists
                    owner = None
                    if prop_data.get('owner_name') or prop_data.get('owner_phone'):
                        owner = Owner(
                            name=prop_data.get('owner_name'),
                            phone=prop_data.get('owner_phone'),
                            email=prop_data.get('owner_email')
                        )
                        self.session.add(owner)
                        self.session.flush()
                    
                    # Calculate distress score
                    distress_score = len(prop_data.get('distress_indicators', [])) * 10
                    if prop_data.get('days_on_market', 0) > 60:
                        distress_score += 20
                    
                    # Create property record
                    property = Property(
                        address=prop_data['address'],
                        zipcode=prop_data['zipcode'],
                        price=prop_data['price'],
                        bedrooms=prop_data.get('bedrooms'),
                        bathrooms=prop_data.get('bathrooms'),
                        square_feet=prop_data.get('square_feet'),
                        property_type='single_family',
                        listing_date=prop_data['listing_date'],
                        source=prop_data['source'],
                        source_url=prop_data['source_url'],
                        owner_id=owner.id if owner else None,
                        distress_score=distress_score,
                        days_on_market=prop_data.get('days_on_market')
                    )
                    
                    self.session.add(property)
                    self.logger.info(f"Added new property: {prop_data['address']}")
                
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

proxy_list = [
    "http://user:pass@proxy1.com:8080",
    "http://user:pass@proxy2.com:8080"
]
scraper = ZillowScraper(session, use_proxies=True, proxy_list=proxy_list) 
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
OUTPUT_DIR = os.path.join(DATA_DIR, 'output')

# Scraping settings
ZILLOW_BASE_URL = "https://www.zillow.com/fsbo/"
FACEBOOK_BASE_URL = "https://www.facebook.com/marketplace"
CRAIGSLIST_BASE_URL = "https://www.craigslist.org"

# Browser settings
HEADLESS = True
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

# Export settings
CSV_EXPORT_PATH = os.path.join(OUTPUT_DIR, 'leads.csv')
EXPORT_FREQUENCY = "daily"  # Options: hourly, daily, weekly

# Scheduler settings
SCHEDULE_INTERVAL = {
    'zillow': '12h',
    'facebook': '12h',
    'craigslist': '12h',
    'public_records': '24h'
}

# Dashboard settings
DASHBOARD_HOST = "127.0.0.1"
DASHBOARD_PORT = 8000

# Logging settings
LOG_LEVEL = "INFO"
LOG_FILE = os.path.join(BASE_DIR, 'app.log')

# Database settings
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///data/properties.db')

# API Keys
ZILLOW_API_KEY = os.getenv('ZILLOW_API_KEY')
GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')

# Search settings
DEFAULT_SEARCH_RADIUS = 5  # miles
MAX_SEARCH_RADIUS = 50  # miles
MIN_DAYS_ON_MARKET = 30
MAX_PROPERTIES_PER_SEARCH = 100

# Distress indicators weights (0-100)
DISTRESS_WEIGHTS = {
    'days_on_market': 30,
    'price_reduced': 20,
    'foreclosure': 100,
    'probate': 90,
    'vacant': 40,
    'tax_delinquent': 80,
    'code_violations': 60,
    'absentee_owner': 30,
}

# Property types to search
PROPERTY_TYPES = [
    'single_family',
    'multi_family',
    'townhouse',
    'condo',
    'mobile_home',
    'land'
]

# Keywords indicating distressed properties
DISTRESS_KEYWORDS = [
    'foreclosure',
    'bank owned',
    'reo',
    'short sale',
    'as-is',
    'fixer',
    'needs work',
    'handyman',
    'distressed',
    'estate sale',
    'probate',
    'must sell',
    'motivated',
] 
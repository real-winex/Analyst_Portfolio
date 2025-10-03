import os
import shutil
from pathlib import Path

def create_directory_structure():
    """Create the necessary directory structure for the project"""
    directories = [
        'scrapers',
        'utils',
        'scheduler',
        'dashboard',
        'dashboard/templates',
        'config',
        'data/output'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory}")

def create_env_file():
    """Create a .env file from .env.example if it doesn't exist"""
    env_example = """# Scraping Settings
MAX_PAGES=3
SCRAPE_DELAY=2
LOAD_TIMEOUT=10

# Location Settings
DEFAULT_LOCATION=los-angeles-ca

# Export Settings
EXPORT_FORMAT=csv
EXPORT_FREQUENCY=daily

# Dashboard Settings
DASHBOARD_HOST=127.0.0.1
DASHBOARD_PORT=8000

# Logging Settings
LOG_LEVEL=INFO
LOG_ROTATION=1 day"""

    if not os.path.exists('.env'):
        with open('.env', 'w') as f:
            f.write(env_example)
        print("Created .env file")
    else:
        print(".env file already exists")

def main():
    """Main setup function"""
    print("Setting up AI-Assisted Real Estate Lead Bot...")
    
    # Create directory structure
    create_directory_structure()
    
    # Create environment file
    create_env_file()
    
    print("\nSetup complete! Next steps:")
    print("1. Edit the .env file with your settings")
    print("2. Install dependencies: pip install -r requirements.txt")
    print("3. Run the Zillow scraper: python scrapers/zillow.py")

if __name__ == "__main__":
    main() 
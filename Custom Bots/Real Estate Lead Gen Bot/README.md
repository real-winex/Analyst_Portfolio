# AI-Assisted Real Estate Lead Bot

An automated system for gathering real estate leads from various sources including Zillow FSBO, Facebook Marketplace, Craigslist, and public records.

## Features

- Zillow FSBO Scraper
- Facebook Marketplace Viewer
- Craigslist FSBO Scraper
- Public Records Parser (Probate/Pre-Foreclosure)
- Lead Cleaning and Deduplication
- Automated Scheduling and Delivery
- Web Dashboard for Monitoring

## Setup

1. Clone this repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env` and fill in your configuration
5. Run the setup script:
   ```bash
   python setup.py
   ```

## Project Structure

```
├── scrapers/
│   ├── zillow.py
│   ├── facebook.py
│   ├── craigslist.py
│   └── public_records.py
├── utils/
│   ├── cleaner.py
│   ├── deduper.py
│   └── export.py
├── scheduler/
│   └── tasks.py
├── dashboard/
│   ├── app.py
│   └── templates/
├── config/
│   └── settings.py
└── data/
    └── output/
```

## Usage

1. Start the scheduler:
   ```bash
   python scheduler/tasks.py
   ```

2. Launch the dashboard:
   ```bash
   python dashboard/app.py
   ```

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

[MIT](https://choosealicense.com/licenses/mit/) 
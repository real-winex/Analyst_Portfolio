# Data Entry Bot

## Overview
The Data Entry Bot is a command-line tool designed to automate form submissions on websites using structured data (e.g., Excel sheets). It supports multiple websites and document types, making it ideal for repetitive data entry tasks.

## Features
- Read data from Excel files
- Automate form submissions on multiple websites
- Support for various document types
- Command-line interface for easy integration

## Requirements
- Python 3.8 or higher
- Dependencies listed in `requirements.txt`

## Installation
1. Clone the repository:
   ```
   git clone <repository-url>
   cd data-entry-bot
   ```
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage
Run the bot using the command:
```
python bot.py --input <path-to-excel-file> [--website <website-url>] [--output <output-file-path>]
```
- `--input`: Path to the Excel file containing data (required).
- `--website`: URL of the website to submit the form (optional). If omitted, the bot will only read the Excel file without submitting to a website.
- `--output`: Path to the output file to save results (optional). If provided, the bot will write the results to this file.

## Configuration
- Update the `.env` file with your credentials if required.

## License
MIT 

## Next Milestones (Planned)
- Add data validation and formatting rules.
- Support for bulk exports in different formats.
- Template matching and schema normalization.
- Robust error handling and reporting. 
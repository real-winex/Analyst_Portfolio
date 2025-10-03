import argparse
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
from dotenv import load_dotenv
import json
import logging

# Load environment variables
load_dotenv()

def read_excel(file_path):
    """Read data from an Excel file."""
    return pd.read_excel(file_path)

def setup_driver():
    """Set up and return a configured Chrome WebDriver."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def submit_form(driver, website_url, data):
    """Submit form data to the specified website."""
    driver.get(website_url)
    # Wait for the form to load
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "form")))
    # Example: Fill form fields (adjust selectors as needed)
    for index, row in data.iterrows():
        # Example: driver.find_element(By.NAME, "field_name").send_keys(row["column_name"])
        pass
    # Example: Submit the form
    # driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    time.sleep(2)  # Wait for submission to complete

def validate_data(data):
    """Validate the data from the Excel file using configuration from config.json."""
    if data.empty:
        raise ValueError("Excel file is empty.")
    # Load required columns from config.json
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
            required_columns = config.get("required_columns", [])
    except FileNotFoundError:
        raise ValueError("Configuration file 'config.json' not found.")
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON in 'config.json'.")

    for col in required_columns:
        if col not in data.columns:
            raise ValueError(f"Required column '{col}' not found in Excel file.")
        if data[col].isnull().any():
            raise ValueError(f"Column '{col}' contains missing values.")
    return data

def export_data(data, output_path, format="csv"):
    """Export data to the specified format (csv, json, excel)."""
    if format.lower() == "csv":
        data.to_csv(output_path, index=False)
    elif format.lower() == "json":
        data.to_json(output_path, orient="records")
    elif format.lower() == "excel":
        data.to_excel(output_path, index=False)
    else:
        raise ValueError(f"Unsupported format: {format}")

def normalize_schema(data):
    """Normalize the schema of the data based on a mapping defined in config.json."""
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
            column_mapping = config.get("column_mapping", {})
    except FileNotFoundError:
        raise ValueError("Configuration file 'config.json' not found.")
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON in 'config.json'.")

    # Rename columns based on the mapping
    data = data.rename(columns=column_mapping)
    return data

def log_error(error_message):
    """Log error messages to a file."""
    logging.basicConfig(filename="error.log", level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s")
    logging.error(error_message)

def main():
    parser = argparse.ArgumentParser(description="Data Entry Bot for automating form submissions.")
    parser.add_argument("--input", required=True, help="Path to the Excel file containing data.")
    parser.add_argument("--website", required=False, help="URL of the website to submit the form (optional).")
    parser.add_argument("--output", required=False, help="Path to the output file to save results (optional).")
    parser.add_argument("--format", required=False, default="csv", help="Output format (csv, json, excel). Default is csv.")
    args = parser.parse_args()

    try:
        data = read_excel(args.input)
        data = validate_data(data)  # Validate data before processing
        data = normalize_schema(data)  # Normalize schema

        if args.website:
            driver = setup_driver()
            try:
                submit_form(driver, args.website, data)
            finally:
                driver.quit()
        else:
            print("No website URL provided. Bot will only read the Excel file.")

        if args.output:
            export_data(data, args.output, args.format)
            print(f"Results saved to {args.output} in {args.format} format.")

    except Exception as e:
        error_message = f"An error occurred: {str(e)}"
        print(error_message)
        log_error(error_message)

if __name__ == "__main__":
    main() 
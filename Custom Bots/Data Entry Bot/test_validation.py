import pandas as pd
import os
from bot import validate_data

def test_validation():
    # Create a valid Excel file
    valid_data = pd.DataFrame({
        "column1": [1, 2, 3],
        "column2": ["a", "b", "c"]
    })
    valid_file = "valid_data.xlsx"
    valid_data.to_excel(valid_file, index=False)

    # Create an invalid Excel file (missing required column)
    invalid_data = pd.DataFrame({
        "column1": [1, 2, 3]
    })
    invalid_file = "invalid_data.xlsx"
    invalid_data.to_excel(invalid_file, index=False)

    # Test valid data
    try:
        data = pd.read_excel(valid_file)
        validate_data(data)
        print("✅ Valid data test passed.")
    except Exception as e:
        print(f"❌ Valid data test failed: {e}")

    # Test invalid data
    try:
        data = pd.read_excel(invalid_file)
        validate_data(data)
        print("❌ Invalid data test failed: Expected an error.")
    except ValueError as e:
        print(f"✅ Invalid data test passed: {e}")

    # Clean up test files
    os.remove(valid_file)
    os.remove(invalid_file)

if __name__ == "__main__":
    test_validation() 
# Data Analytics Bot

An automated data analysis tool that processes CSV and Excel files to generate insights, visualizations, and reports.

## Features

1. **Data Ingestion**
   - Supports CSV and Excel files
   - Automatic data type detection
   - Missing value handling

2. **Exploratory Data Analysis (EDA)**
   - Automatic column type detection
   - Descriptive statistics
   - Correlation analysis
   - Missing value analysis

3. **Data Visualization**
   - Automatic chart generation based on data types
   - Bar charts for categorical data
   - Histograms for numerical data
   - Line charts for time series data
   - Correlation heatmaps

4. **AI-Powered Insights**
   - Automated text summaries of key findings
   - Trend analysis
   - Anomaly detection

5. **Export Options**
   - JSON format for machine-readable insights
   - PDF reports with visualizations
   - Interactive dashboards (coming soon)

## Installation

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Basic usage:
```bash
python analyze.py --input your_data.csv --report pdf --dashboard true
```

### Command Line Arguments

- `--input`: Path to input file (CSV or Excel) [required]
- `--report`: Report format (pdf or json) [default: pdf]
- `--dashboard`: Generate interactive dashboard [flag]

### Example

```bash
# Generate PDF report
python analyze.py --input sales_data.csv --report pdf

# Generate JSON insights
python analyze.py --input sales_data.csv --report json

# Generate dashboard
python analyze.py --input sales_data.csv --dashboard
```

## Output

The tool generates the following outputs:

1. `insights.json`: Contains all statistical analysis and insights
2. `summary.pdf`: PDF report with visualizations (when --report pdf is used)
3. Interactive dashboard (when --dashboard is used)

## Requirements

- Python 3.8+
- See requirements.txt for full list of dependencies

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 
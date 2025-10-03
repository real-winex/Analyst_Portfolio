import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from sklearn.impute import SimpleImputer, KNNImputer
from sklearn.preprocessing import StandardScaler, MinMaxScaler
import re
from datetime import datetime
import logging
import json
from pathlib import Path

class DataCleaner:
    def __init__(self, data: pd.DataFrame, quality_report: Optional[Dict] = None):
        self.original_data = data.copy()
        self.data = data.copy()
        self.quality_report = quality_report
        self.cleaning_steps = []
        self.cleaning_summary = {
            'rows_removed': 0,
            'columns_cleaned': [],
            'transformations_applied': []
        }
        
    def clean_data(self, strategy: str = 'auto') -> pd.DataFrame:
        """
        Clean the dataset based on the quality report or specified strategy
        
        Parameters:
        -----------
        strategy : str
            'auto' - Use quality report to determine cleaning steps
            'basic' - Apply only basic cleaning (missing values, duplicates)
            'aggressive' - Apply all cleaning steps including outlier removal
        """
        if strategy == 'auto' and self.quality_report:
            self._clean_based_on_quality_report()
        elif strategy == 'basic':
            self._apply_basic_cleaning()
        elif strategy == 'aggressive':
            self._apply_aggressive_cleaning()
        else:
            self._apply_basic_cleaning()
            
        return self.data
    
    def _clean_based_on_quality_report(self):
        """Apply cleaning steps based on quality report findings"""
        if not self.quality_report:
            return
            
        # Handle missing values
        if 'missing_values' in self.quality_report['metrics']:
            self._handle_missing_values()
            
        # Handle duplicates
        if 'duplicates' in self.quality_report['metrics']:
            self._handle_duplicates()
            
        # Handle outliers
        if 'outliers' in self.quality_report['metrics']:
            self._handle_outliers()
            
        # Handle data type issues
        if 'data_types' in self.quality_report['metrics']:
            self._handle_data_types()
    
    def _apply_basic_cleaning(self):
        """Apply basic cleaning steps"""
        self._handle_missing_values()
        self._handle_duplicates()
        self._standardize_column_names()
    
    def _apply_aggressive_cleaning(self):
        """Apply all cleaning steps including outlier removal"""
        self._apply_basic_cleaning()
        self._handle_outliers()
        self._handle_data_types()
        self._normalize_numeric_columns()
    
    def _handle_missing_values(self):
        """Handle missing values using appropriate imputation methods"""
        for col in self.data.columns:
            missing_count = self.data[col].isnull().sum()
            if missing_count > 0:
                if self.data[col].dtype in ['int64', 'float64']:
                    # Use KNN imputation for numeric columns
                    imputer = KNNImputer(n_neighbors=5)
                    self.data[col] = imputer.fit_transform(self.data[[col]])
                    self.cleaning_steps.append(f"Imputed {missing_count} missing values in {col} using KNN")
                else:
                    # Use mode imputation for categorical columns
                    mode_value = self.data[col].mode()[0]
                    self.data[col] = self.data[col].fillna(mode_value)
                    self.cleaning_steps.append(f"Imputed {missing_count} missing values in {col} using mode")
    
    def _handle_duplicates(self):
        """Remove duplicate rows"""
        original_rows = len(self.data)
        self.data = self.data.drop_duplicates()
        removed_rows = original_rows - len(self.data)
        if removed_rows > 0:
            self.cleaning_steps.append(f"Removed {removed_rows} duplicate rows")
            self.cleaning_summary['rows_removed'] += removed_rows
    
    def _handle_outliers(self):
        """Handle outliers in numeric columns"""
        for col in self.data.select_dtypes(include=[np.number]).columns:
            Q1 = self.data[col].quantile(0.25)
            Q3 = self.data[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            # Replace outliers with bounds
            outliers = ((self.data[col] < lower_bound) | (self.data[col] > upper_bound))
            if outliers.any():
                self.data.loc[outliers, col] = self.data[col].clip(lower_bound, upper_bound)
                self.cleaning_steps.append(f"Clipped {outliers.sum()} outliers in {col}")
    
    def _handle_data_types(self):
        """Fix data type issues"""
        for col in self.data.columns:
            # Try to convert string numbers to numeric
            if self.data[col].dtype == 'object':
                try:
                    self.data[col] = pd.to_numeric(self.data[col])
                    self.cleaning_steps.append(f"Converted {col} to numeric type")
                except:
                    # Try to convert to datetime
                    try:
                        self.data[col] = pd.to_datetime(self.data[col])
                        self.cleaning_steps.append(f"Converted {col} to datetime type")
                    except:
                        # Clean string values
                        self.data[col] = self.data[col].astype(str).str.strip()
                        self.cleaning_steps.append(f"Cleaned string values in {col}")
    
    def _standardize_column_names(self):
        """Standardize column names"""
        new_columns = {}
        for col in self.data.columns:
            # Convert to lowercase
            new_col = col.lower()
            # Replace spaces and special characters with underscores
            new_col = re.sub(r'[^a-z0-9]+', '_', new_col)
            # Remove leading/trailing underscores
            new_col = new_col.strip('_')
            new_columns[col] = new_col
        
        self.data = self.data.rename(columns=new_columns)
        self.cleaning_steps.append("Standardized column names")
    
    def _normalize_numeric_columns(self):
        """Normalize numeric columns"""
        numeric_cols = self.data.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            scaler = StandardScaler()
            self.data[numeric_cols] = scaler.fit_transform(self.data[numeric_cols])
            self.cleaning_steps.append("Normalized numeric columns")
    
    def get_cleaning_summary(self) -> Dict:
        """Get summary of cleaning operations performed"""
        return {
            'original_shape': self.original_data.shape,
            'cleaned_shape': self.data.shape,
            'rows_removed': self.cleaning_summary['rows_removed'],
            'cleaning_steps': self.cleaning_steps,
            'columns_cleaned': list(set(self.cleaning_summary['columns_cleaned'])),
            'transformations_applied': self.cleaning_summary['transformations_applied']
        }
    
    def save_cleaned_data(self, output_path: str):
        """Save cleaned data to file"""
        file_ext = Path(output_path).suffix.lower()
        if file_ext == '.csv':
            self.data.to_csv(output_path, index=False)
        elif file_ext in ['.xlsx', '.xls']:
            self.data.to_excel(output_path, index=False)
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")
        
        # Save cleaning summary
        summary_path = str(Path(output_path).with_suffix('.json'))
        with open(summary_path, 'w') as f:
            json.dump(self.get_cleaning_summary(), f, indent=4)
        
        return output_path, summary_path 
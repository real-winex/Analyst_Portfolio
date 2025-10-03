import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

class DataQualityAnalyzer:
    def __init__(self, data: pd.DataFrame):
        self.data = data
        self.quality_metrics = {}
        self.issues = []
        self.recommendations = []
        
    def analyze_quality(self) -> Dict:
        """Perform comprehensive data quality analysis"""
        self._check_missing_values()
        self._check_duplicates()
        self._check_data_types()
        self._check_outliers()
        self._check_consistency()
        self._generate_recommendations()
        
        return {
            'metrics': self.quality_metrics,
            'issues': self.issues,
            'recommendations': self.recommendations
        }
    
    def _check_missing_values(self):
        """Analyze missing values in the dataset"""
        missing_stats = self.data.isnull().sum()
        missing_percentage = (missing_stats / len(self.data)) * 100
        
        self.quality_metrics['missing_values'] = {
            'total_missing': missing_stats.sum(),
            'missing_by_column': missing_stats.to_dict(),
            'missing_percentage': missing_percentage.to_dict()
        }
        
        # Identify columns with significant missing values
        high_missing = missing_percentage[missing_percentage > 30]
        if not high_missing.empty:
            self.issues.append({
                'type': 'missing_values',
                'severity': 'high',
                'description': f'Columns with >30% missing values: {", ".join(high_missing.index)}'
            })
    
    def _check_duplicates(self):
        """Check for duplicate rows and values"""
        duplicate_rows = self.data.duplicated().sum()
        duplicate_values = {}
        
        for col in self.data.columns:
            if self.data[col].dtype in ['object', 'category']:
                duplicate_values[col] = self.data[col].value_counts()
                duplicate_values[col] = duplicate_values[col][duplicate_values[col] > 1]
        
        self.quality_metrics['duplicates'] = {
            'duplicate_rows': duplicate_rows,
            'duplicate_values': duplicate_values
        }
        
        if duplicate_rows > 0:
            self.issues.append({
                'type': 'duplicates',
                'severity': 'medium',
                'description': f'Found {duplicate_rows} duplicate rows'
            })
    
    def _check_data_types(self):
        """Analyze data types and potential type issues"""
        type_info = {}
        for col in self.data.columns:
            type_info[col] = {
                'dtype': str(self.data[col].dtype),
                'unique_values': self.data[col].nunique(),
                'sample_values': self.data[col].dropna().head(3).tolist()
            }
            
            # Check for mixed types in object columns
            if self.data[col].dtype == 'object':
                try:
                    self.data[col].astype(float)
                    self.issues.append({
                        'type': 'mixed_types',
                        'severity': 'low',
                        'description': f'Column {col} contains numeric values stored as strings'
                    })
                except:
                    pass
        
        self.quality_metrics['data_types'] = type_info
    
    def _check_outliers(self):
        """Detect outliers in numeric columns"""
        outliers = {}
        for col in self.data.select_dtypes(include=[np.number]).columns:
            Q1 = self.data[col].quantile(0.25)
            Q3 = self.data[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            outlier_count = ((self.data[col] < lower_bound) | (self.data[col] > upper_bound)).sum()
            if outlier_count > 0:
                outliers[col] = {
                    'count': outlier_count,
                    'percentage': (outlier_count / len(self.data)) * 100,
                    'bounds': {'lower': lower_bound, 'upper': upper_bound}
                }
                
                if outlier_count > len(self.data) * 0.1:  # More than 10% outliers
                    self.issues.append({
                        'type': 'outliers',
                        'severity': 'medium',
                        'description': f'Column {col} has {outlier_count} outliers ({outlier_count/len(self.data)*100:.1f}%)'
                    })
        
        self.quality_metrics['outliers'] = outliers
    
    def _check_consistency(self):
        """Check for data consistency issues"""
        consistency_issues = []
        
        # Check for inconsistent date formats
        date_columns = self.data.select_dtypes(include=['datetime64']).columns
        for col in date_columns:
            if self.data[col].dt.year.min() < 1900 or self.data[col].dt.year.max() > 2100:
                consistency_issues.append(f'Column {col} contains dates outside reasonable range')
        
        # Check for inconsistent categorical values
        cat_columns = self.data.select_dtypes(include=['object', 'category']).columns
        for col in cat_columns:
            unique_values = self.data[col].unique()
            if len(unique_values) < len(self.data) * 0.01:  # Less than 1% unique values
                consistency_issues.append(f'Column {col} has very few unique values for its size')
        
        if consistency_issues:
            self.issues.append({
                'type': 'consistency',
                'severity': 'low',
                'description': '; '.join(consistency_issues)
            })
    
    def _generate_recommendations(self):
        """Generate recommendations based on identified issues"""
        for issue in self.issues:
            if issue['type'] == 'missing_values':
                self.recommendations.append({
                    'issue': 'Missing Values',
                    'recommendation': 'Consider imputation methods or removing rows/columns with high missing values',
                    'priority': 'high' if issue['severity'] == 'high' else 'medium'
                })
            elif issue['type'] == 'duplicates':
                self.recommendations.append({
                    'issue': 'Duplicate Data',
                    'recommendation': 'Review and remove duplicate rows if they are not legitimate duplicates',
                    'priority': 'medium'
                })
            elif issue['type'] == 'outliers':
                self.recommendations.append({
                    'issue': 'Outliers',
                    'recommendation': 'Investigate outliers to determine if they are errors or legitimate extreme values',
                    'priority': 'medium'
                })
            elif issue['type'] == 'consistency':
                self.recommendations.append({
                    'issue': 'Data Consistency',
                    'recommendation': 'Standardize data formats and review categorical values for consistency',
                    'priority': 'low'
                })
    
    def generate_quality_report(self) -> Dict:
        """Generate a comprehensive data quality report"""
        quality_analysis = self.analyze_quality()
        
        # Calculate overall quality score
        total_issues = len(self.issues)
        severity_weights = {'high': 3, 'medium': 2, 'low': 1}
        weighted_score = sum(severity_weights[issue['severity']] for issue in self.issues)
        
        quality_score = max(0, 100 - (weighted_score * 10))
        
        return {
            'quality_score': quality_score,
            'total_issues': total_issues,
            'issues_by_severity': {
                'high': len([i for i in self.issues if i['severity'] == 'high']),
                'medium': len([i for i in self.issues if i['severity'] == 'medium']),
                'low': len([i for i in self.issues if i['severity'] == 'low'])
            },
            'metrics': self.quality_metrics,
            'issues': self.issues,
            'recommendations': self.recommendations
        }
    
    def create_quality_visualizations(self) -> Dict[str, go.Figure]:
        """Create visualizations for data quality metrics"""
        visualizations = {}
        
        # Missing values heatmap
        missing_data = self.data.isnull()
        fig_missing = px.imshow(
            missing_data,
            title='Missing Values Heatmap',
            labels=dict(x='Columns', y='Rows', color='Missing'),
            color_continuous_scale=['white', 'red']
        )
        visualizations['missing_heatmap'] = fig_missing
        
        # Data type distribution
        type_counts = pd.Series([str(dtype) for dtype in self.data.dtypes]).value_counts()
        fig_types = px.pie(
            values=type_counts.values,
            names=type_counts.index,
            title='Data Type Distribution'
        )
        visualizations['type_distribution'] = fig_types
        
        # Outlier box plots for numeric columns
        numeric_cols = self.data.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            fig_outliers = make_subplots(rows=len(numeric_cols), cols=1)
            for i, col in enumerate(numeric_cols, 1):
                fig_outliers.add_trace(
                    go.Box(y=self.data[col], name=col),
                    row=i, col=1
                )
            fig_outliers.update_layout(height=300*len(numeric_cols), title='Outlier Analysis')
            visualizations['outlier_analysis'] = fig_outliers
        
        return visualizations 
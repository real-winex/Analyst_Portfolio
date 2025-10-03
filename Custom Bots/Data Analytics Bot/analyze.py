#!/usr/bin/env python3

import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
from pathlib import Path
import json
from datetime import datetime
import os
from dotenv import load_dotenv
from pdf_report import generate_pdf_report
from dashboard import run_dashboard
from template_analyzer import generate_dashboard_from_template
from data_quality import DataQualityAnalyzer
from data_cleaning import DataCleaner
import openai
from tqdm import tqdm
import time
import sys

# Load environment variables
load_dotenv()

class ProgressTracker:
    def __init__(self, total_steps):
        self.total_steps = total_steps
        self.current_step = 0
        self.start_time = time.time()
        
    def update(self, message):
        self.current_step += 1
        elapsed = time.time() - self.start_time
        progress = (self.current_step / self.total_steps) * 100
        sys.stdout.write(f"\r[{self.current_step}/{self.total_steps}] {message} ({progress:.1f}%) - {elapsed:.1f}s")
        sys.stdout.flush()
        
    def complete(self):
        total_time = time.time() - self.start_time
        sys.stdout.write(f"\nAnalysis completed in {total_time:.1f} seconds\n")
        sys.stdout.flush()

class DataAnalyzer:
    def __init__(self, input_file, report_format='pdf', dashboard=False, template_image=None, 
                 quality_check=True, clean_data=False, cleaning_strategy='auto'):
        self.input_file = input_file
        self.report_format = report_format.lower()
        self.dashboard = dashboard
        self.template_image = template_image
        self.quality_check = quality_check
        self.clean_data = clean_data
        self.cleaning_strategy = cleaning_strategy
        self.data = None
        self.column_types = {}
        self.insights = {}
        self.quality_report = None
        self.cleaned_data = None
        self.cleaning_summary = None
        
    def load_data(self):
        """Load data from CSV or Excel file"""
        print("\nStarting data analysis...")
        print(f"Input file: {self.input_file}")
        
        file_ext = Path(self.input_file).suffix.lower()
        if file_ext == '.csv':
            self.data = pd.read_csv(self.input_file)
        elif file_ext in ['.xlsx', '.xls']:
            self.data = pd.read_excel(self.input_file)
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")
        
        print(f"Loaded {len(self.data)} rows and {len(self.data.columns)} columns")
        self._detect_column_types()
        
        # Perform data quality analysis if requested
        if self.quality_check:
            print("\nPerforming data quality analysis...")
            quality_analyzer = DataQualityAnalyzer(self.data)
            self.quality_report = quality_analyzer.generate_quality_report()
            
            # Print quality score and issues
            print(f"\nData Quality Score: {self.quality_report['quality_score']:.1f}/100")
            if self.quality_report['total_issues'] > 0:
                print("\nData Quality Issues Found:")
                for issue in self.quality_report['issues']:
                    print(f"- [{issue['severity'].upper()}] {issue['description']}")
                
                print("\nRecommendations:")
                for rec in self.quality_report['recommendations']:
                    print(f"- [{rec['priority'].upper()}] {rec['recommendation']}")
        
        # Clean data if requested
        if self.clean_data:
            print("\nCleaning data...")
            cleaner = DataCleaner(self.data, self.quality_report)
            self.cleaned_data = cleaner.clean_data(strategy=self.cleaning_strategy)
            self.cleaning_summary = cleaner.get_cleaning_summary()
            
            # Print cleaning summary
            print("\nData Cleaning Summary:")
            print(f"Original shape: {self.cleaning_summary['original_shape']}")
            print(f"Cleaned shape: {self.cleaning_summary['cleaned_shape']}")
            print(f"Rows removed: {self.cleaning_summary['rows_removed']}")
            print("\nCleaning steps applied:")
            for step in self.cleaning_summary['cleaning_steps']:
                print(f"- {step}")
            
            # Save cleaned data
            output_path = str(Path(self.input_file).with_name(f"cleaned_{Path(self.input_file).name}"))
            cleaner.save_cleaned_data(output_path)
            print(f"\nCleaned data saved to: {output_path}")
            
            # Use cleaned data for further analysis
            self.data = self.cleaned_data
        
        return self.data
    
    def _detect_column_types(self):
        """Detect and store column types"""
        for col in self.data.columns:
            if pd.api.types.is_numeric_dtype(self.data[col]):
                self.column_types[col] = 'numerical'
            elif pd.api.types.is_datetime64_dtype(self.data[col]):
                self.column_types[col] = 'date'
            else:
                self.column_types[col] = 'categorical'
    
    def generate_descriptive_stats(self):
        """Generate descriptive statistics"""
        stats = {
            'numerical': {},
            'categorical': {},
            'missing_values': self.data.isnull().sum().to_dict()
        }
        
        # Numerical columns
        num_cols = [col for col, type_ in self.column_types.items() if type_ == 'numerical']
        if num_cols:
            stats['numerical'] = self.data[num_cols].describe().to_dict()
        
        # Categorical columns
        cat_cols = [col for col, type_ in self.column_types.items() if type_ == 'categorical']
        if cat_cols:
            for col in cat_cols:
                stats['categorical'][col] = self.data[col].value_counts().to_dict()
        
        return stats
    
    def generate_correlation_heatmap(self):
        """Generate correlation heatmap for numerical columns"""
        num_cols = [col for col, type_ in self.column_types.items() if type_ == 'numerical']
        if len(num_cols) > 1:
            corr_matrix = self.data[num_cols].corr()
            plt.figure(figsize=(10, 8))
            sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0)
            plt.title('Correlation Heatmap')
            return plt
        return None
    
    def generate_visualizations(self):
        """Generate appropriate visualizations based on column types"""
        visualizations = {}
        
        # Generate visualizations for each column type
        for col, type_ in self.column_types.items():
            if type_ == 'categorical':
                # Bar chart for categorical
                fig = px.bar(self.data[col].value_counts(), title=f'Distribution of {col}')
                visualizations[f'{col}_bar'] = fig
            
            elif type_ == 'numerical':
                # Histogram for numerical
                fig = px.histogram(self.data, x=col, title=f'Distribution of {col}')
                visualizations[f'{col}_hist'] = fig
            
            elif type_ == 'date':
                # Line chart for date
                if len(self.data[col].unique()) > 1:
                    fig = px.line(self.data.groupby(col).size().reset_index(), 
                                x=col, y=0, title=f'Trend over time for {col}')
                    visualizations[f'{col}_line'] = fig
        
        return visualizations
    
    def generate_ai_summary(self):
        """Generate AI-powered text summary of insights with actionable recommendations"""
        try:
            # Prepare data summary for AI
            stats = self.generate_descriptive_stats()
            summary = {
                'dataset_info': {
                    'rows': len(self.data),
                    'columns': len(self.data.columns),
                    'column_types': self.column_types,
                    'missing_values': self.data.isnull().sum().to_dict()
                },
                'numerical_stats': stats['numerical'],
                'categorical_stats': stats['categorical']
            }
            
            # Create comprehensive prompt for OpenAI
            prompt = f"""Analyze this dataset and provide comprehensive insights and actionable recommendations:
            {json.dumps(summary, indent=2)}
            
            Please provide a detailed analysis including:
            
            1. Key Findings:
               - Data quality assessment
               - Notable patterns and trends
               - Statistical insights
               - Business implications
            
            2. Actionable Recommendations:
               - Immediate actions to take
               - Short-term improvements (1-3 months)
               - Long-term strategies (3-12 months)
               - Success metrics to track
            
            3. Implementation Plan:
               - Step-by-step action items
               - Required resources
               - Timeline suggestions
               - Risk mitigation strategies
            
            Format the response in a clear, professional manner suitable for a business report.
            Focus on practical, implementable solutions and concrete next steps."""
            
            # Call OpenAI API
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a data analysis expert providing comprehensive insights and actionable recommendations for a business report."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            # Store the AI insights
            self.insights = {
                'summary': response.choices[0].message.content,
                'timestamp': datetime.now().isoformat()
            }
            
            return self.insights
            
        except Exception as e:
            print(f"Error generating AI summary: {str(e)}")
            return {
                'summary': "AI summary generation failed. Please check your OpenAI API configuration.",
                'timestamp': datetime.now().isoformat()
            }
    
    def export_results(self):
        """Export results in specified format"""
        # Initialize progress tracker
        total_steps = 4  # Basic steps
        if self.quality_check:
            total_steps += 1
        if self.clean_data:
            total_steps += 1
        if self.report_format == 'pdf':
            total_steps += 1
        if self.dashboard:
            total_steps += 1
            
        progress = ProgressTracker(total_steps)
        
        # Prepare results dictionary
        results = {
            'descriptive_stats': self.generate_descriptive_stats(),
            'column_types': self.column_types,
            'timestamp': datetime.now().isoformat()
        }
        progress.update("Generated descriptive statistics")
        
        # Add quality report if available
        if self.quality_report:
            results['quality_report'] = self.quality_report
            progress.update("Added quality report")
        
        # Add cleaning summary if available
        if self.cleaning_summary:
            results['cleaning_summary'] = self.cleaning_summary
            progress.update("Added cleaning summary")
        
        # Generate AI insights
        print("\nGenerating AI insights...")
        ai_insights = self.generate_ai_summary()
        results['ai_insights'] = ai_insights
        progress.update("Generated AI insights")
        
        # Export to JSON
        with open('insights.json', 'w') as f:
            json.dump(results, f, indent=4)
        progress.update("Exported results to JSON")
        
        # Generate visualizations
        print("\nGenerating visualizations...")
        visualizations = self.generate_visualizations()
        progress.update("Created visualizations")
        
        # Export to PDF if requested
        if self.report_format == 'pdf':
            print("\nGenerating PDF report...")
            pdf_path = generate_pdf_report(self)
            print(f"PDF report generated: {pdf_path}")
            progress.update("Generated PDF report")
        
        # Create dashboard if requested
        if self.dashboard:
            if self.template_image:
                print("\nGenerating dashboard from template...")
                generate_dashboard_from_template(self.template_image, self.data)
                progress.update("Created template-based dashboard")
            else:
                print("\nStarting standard interactive dashboard...")
                run_dashboard(self)
                progress.update("Started interactive dashboard")
        
        progress.complete()
        return results

def main():
    parser = argparse.ArgumentParser(description='Data Analytics Bot')
    parser.add_argument('--input', required=True, help='Input file path (CSV or Excel)')
    parser.add_argument('--report', default='pdf', choices=['pdf', 'json'], help='Report format')
    parser.add_argument('--dashboard', action='store_true', help='Generate interactive dashboard')
    parser.add_argument('--template', help='Path to dashboard template image')
    parser.add_argument('--port', type=int, default=8050, help='Port for the dashboard (default: 8050)')
    parser.add_argument('--no-quality-check', action='store_true', help='Skip data quality analysis')
    parser.add_argument('--clean', action='store_true', help='Clean the data')
    parser.add_argument('--cleaning-strategy', default='auto', 
                       choices=['auto', 'basic', 'aggressive'],
                       help='Data cleaning strategy (default: auto)')
    
    args = parser.parse_args()
    
    try:
        analyzer = DataAnalyzer(
            input_file=args.input,
            report_format=args.report,
            dashboard=args.dashboard,
            template_image=args.template,
            quality_check=not args.no_quality_check,
            clean_data=args.clean,
            cleaning_strategy=args.cleaning_strategy
        )
        
        # Load and analyze data
        analyzer.load_data()
        results = analyzer.export_results()
        
        print(f"\nAnalysis complete! Results exported to insights.json")
        if args.report == 'pdf':
            print("PDF report generated: summary.pdf")
        if args.dashboard:
            if args.template:
                print(f"Template-based dashboard available at: http://localhost:{args.port}")
            else:
                print(f"Standard dashboard available at: http://localhost:{args.port}")
                
    except Exception as e:
        print(f"\nError during analysis: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main() 
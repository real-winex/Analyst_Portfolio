from fpdf import FPDF
import matplotlib.pyplot as plt
import io
import json
from datetime import datetime
import os
import numpy as np
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import seaborn as sns

class PDFReport(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)
        self.add_page()
        # Set default font to Times New Roman
        self.set_font('Times', '', 12)
        
    def header(self):
        # Times New Roman bold 15
        self.set_font('Times', 'B', 15)
        # Move to the right
        self.cell(80)
        # Title
        self.cell(30, 10, 'Data Analysis Report', 0, 0, 'C')
        # Line break
        self.ln(20)
        
    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        # Times New Roman italic 8
        self.set_font('Times', 'I', 8)
        # Page number
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', 0, 0, 'C')
        # Date
        self.cell(-30, 10, datetime.now().strftime('%Y-%m-%d %H:%M'), 0, 0, 'R')

    def add_section_title(self, title):
        self.set_font('Times', 'B', 12)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(5)

    def add_text(self, text):
        self.set_font('Times', '', 12)
        # Add indentation
        self.cell(10, 5, '', 0, 0)
        self.multi_cell(0, 5, text)
        self.ln(5)

    def add_plot(self, plt_figure, caption=None):
        # Save the plot to a bytes buffer
        buf = io.BytesIO()
        plt_figure.savefig(buf, format='png', bbox_inches='tight', dpi=300)
        buf.seek(0)
        
        # Add the plot to the PDF
        self.image(buf, x=10, w=190)
        if caption:
            self.set_font('Times', 'I', 10)
            self.cell(0, 5, caption, 0, 1, 'C')
        self.ln(5)
        
        # Close the buffer
        buf.close()

    def add_table(self, headers, data, col_widths=None):
        # Set font for table
        self.set_font('Times', 'B', 12)
        
        # Default column widths if not provided
        if col_widths is None:
            col_widths = [190 / len(headers)] * len(headers)
        
        # Headers
        for i, header in enumerate(headers):
            self.cell(col_widths[i], 7, str(header), 1, 0, 'C')
        self.ln()
        
        # Data
        self.set_font('Times', '', 12)
        for row in data:
            for i, value in enumerate(row):
                self.cell(col_widths[i], 6, str(value), 1, 0, 'C')
            self.ln()

def generate_pdf_report(analyzer, output_path='summary.pdf'):
    """Generate a PDF report with analysis results"""
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30
    )
    story.append(Paragraph("Data Analysis Report", title_style))
    story.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles["Normal"]))
    story.append(Spacer(1, 12))
    
    # Dataset Overview
    story.append(Paragraph("Dataset Overview", styles["Heading2"]))
    overview_data = [
        ["Total Rows", str(len(analyzer.data))],
        ["Total Columns", str(len(analyzer.data.columns))],
        ["Memory Usage", f"{analyzer.data.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB"]
    ]
    overview_table = Table(overview_data, colWidths=[2*inch, 2*inch])
    overview_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(overview_table)
    story.append(Spacer(1, 12))
    
    # Data Quality Analysis
    if analyzer.quality_report:
        story.append(Paragraph("Data Quality Analysis", styles["Heading2"]))
        
        # Quality Score
        quality_score = analyzer.quality_report['quality_score']
        score_color = colors.green if quality_score >= 80 else colors.orange if quality_score >= 60 else colors.red
        story.append(Paragraph(f"Overall Quality Score: {quality_score:.1f}/100", 
                             ParagraphStyle('Score', textColor=score_color)))
        story.append(Spacer(1, 12))
        
        # Issues Summary
        if analyzer.quality_report['total_issues'] > 0:
            story.append(Paragraph("Quality Issues Found:", styles["Heading3"]))
            issues_data = [["Severity", "Description"]]
            for issue in analyzer.quality_report['issues']:
                issues_data.append([issue['severity'].upper(), issue['description']])
            
            issues_table = Table(issues_data, colWidths=[1.5*inch, 4.5*inch])
            issues_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
            ]))
            story.append(issues_table)
            story.append(Spacer(1, 12))
            
            # Recommendations
            story.append(Paragraph("Recommendations:", styles["Heading3"]))
            recs_data = [["Priority", "Issue", "Recommendation"]]
            for rec in analyzer.quality_report['recommendations']:
                recs_data.append([rec['priority'].upper(), rec['issue'], rec['recommendation']])
            
            recs_table = Table(recs_data, colWidths=[1*inch, 1.5*inch, 3.5*inch])
            recs_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
            ]))
            story.append(recs_table)
            story.append(Spacer(1, 12))
    
    # Column Information
    story.append(Paragraph("Column Information", styles["Heading2"]))
    column_data = [["Column", "Type", "Missing Values", "Unique Values"]]
    for col in analyzer.data.columns:
        missing = analyzer.data[col].isnull().sum()
        unique = analyzer.data[col].nunique()
        column_data.append([col, str(analyzer.data[col].dtype), str(missing), str(unique)])
    
    column_table = Table(column_data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 1.5*inch])
    column_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
    ]))
    story.append(column_table)
    story.append(Spacer(1, 12))
    
    # Descriptive Statistics
    story.append(Paragraph("Descriptive Statistics", styles["Heading2"]))
    stats = analyzer.generate_descriptive_stats()
    
    for col, col_stats in stats.items():
        story.append(Paragraph(f"Column: {col}", styles["Heading3"]))
        stats_data = [[k, str(v)] for k, v in col_stats.items()]
        stats_table = Table(stats_data, colWidths=[2*inch, 2*inch])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
        ]))
        story.append(stats_table)
        story.append(Spacer(1, 12))
    
    # AI-Powered Analysis
    if 'ai_insights' in analyzer.insights:
        story.append(Paragraph("AI-Powered Analysis & Recommendations", styles["Heading2"]))
        story.append(Paragraph(analyzer.insights['ai_insights'], styles["Normal"]))
        story.append(Spacer(1, 12))
    
    # Build PDF
    doc.build(story)
    return os.path.abspath(output_path) 
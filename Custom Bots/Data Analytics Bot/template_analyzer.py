import cv2
import numpy as np
from PIL import Image
import io
import base64
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import dash
from dash import dcc, html
import json

class DashboardTemplateAnalyzer:
    def __init__(self, template_image):
        """Initialize with a dashboard template image"""
        self.template_image = template_image
        self.layout_structure = None
        self.visualization_types = {}
        
    def analyze_template(self):
        """Analyze the template image to determine layout and visualization types"""
        # Convert image to numpy array if it's a base64 string
        if isinstance(self.template_image, str) and self.template_image.startswith('data:image'):
            # Remove the data URL prefix
            image_data = self.template_image.split(',')[1]
            # Decode base64
            image_bytes = base64.b64decode(image_data)
            # Convert to numpy array
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        else:
            # If it's a file path
            img = cv2.imread(self.template_image)
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Detect edges
        edges = cv2.Canny(gray, 50, 150)
        
        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Analyze layout structure
        self.layout_structure = self._analyze_layout(contours, img.shape)
        
        # Detect visualization types
        self.visualization_types = self._detect_visualization_types(img)
        
        return {
            'layout': self.layout_structure,
            'visualization_types': self.visualization_types
        }
    
    def _analyze_layout(self, contours, image_shape):
        """Analyze the layout structure from contours"""
        # Sort contours by area
        contours = sorted(contours, key=cv2.contourArea, reverse=True)
        
        # Get bounding boxes
        boxes = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if w * h > 1000:  # Filter out small elements
                boxes.append({
                    'x': x,
                    'y': y,
                    'width': w,
                    'height': h,
                    'area': w * h
                })
        
        # Determine grid structure
        grid = self._determine_grid(boxes, image_shape)
        
        return {
            'grid': grid,
            'boxes': boxes
        }
    
    def _determine_grid(self, boxes, image_shape):
        """Determine the grid structure from bounding boxes"""
        # Sort boxes by y-coordinate
        boxes.sort(key=lambda b: b['y'])
        
        # Group boxes into rows
        rows = []
        current_row = []
        row_height = 0
        
        for box in boxes:
            if not current_row or abs(box['y'] - current_row[0]['y']) < 50:
                current_row.append(box)
                row_height = max(row_height, box['height'])
            else:
                if current_row:
                    rows.append({
                        'boxes': sorted(current_row, key=lambda b: b['x']),
                        'height': row_height
                    })
                current_row = [box]
                row_height = box['height']
        
        if current_row:
            rows.append({
                'boxes': sorted(current_row, key=lambda b: b['x']),
                'height': row_height
            })
        
        return rows
    
    def _detect_visualization_types(self, image):
        """Detect types of visualizations in the template"""
        # Convert to HSV for better color detection
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # Define color ranges for different visualization types
        color_ranges = {
            'bar_chart': ([0, 0, 200], [180, 30, 255]),  # White-ish
            'line_chart': ([0, 0, 100], [180, 30, 200]),  # Gray-ish
            'pie_chart': ([0, 50, 50], [180, 255, 255])   # Colored
        }
        
        visualization_types = {}
        
        for viz_type, (lower, upper) in color_ranges.items():
            # Create mask for color range
            mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
            
            # Find contours in mask
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Store detected visualizations
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                if w * h > 1000:  # Filter out small elements
                    visualization_types[f"{x}_{y}"] = {
                        'type': viz_type,
                        'position': (x, y, w, h)
                    }
        
        return visualization_types

def create_dashboard_from_template(analyzer, template_analysis, data):
    """Create a dashboard based on template analysis"""
    app = dash.Dash(__name__)
    
    # Create layout based on template analysis
    layout_children = []
    
    # Add header
    layout_children.append(
        html.Div([
            html.H1('Data Analysis Dashboard', 
                   style={'textAlign': 'center', 'color': '#2c3e50', 'marginBottom': 30}),
            html.P(f'Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M")}',
                  style={'textAlign': 'center', 'color': '#7f8c8d'})
        ])
    )
    
    # Create grid layout
    for row in template_analysis['layout']['grid']:
        row_children = []
        for box in row['boxes']:
            # Determine visualization type for this box
            viz_type = None
            for pos, viz in template_analysis['visualization_types'].items():
                if abs(int(pos.split('_')[0]) - box['x']) < 50 and abs(int(pos.split('_')[1]) - box['y']) < 50:
                    viz_type = viz['type']
                    break
            
            # Create appropriate visualization
            if viz_type == 'bar_chart':
                fig = create_bar_chart(data)
            elif viz_type == 'line_chart':
                fig = create_line_chart(data)
            elif viz_type == 'pie_chart':
                fig = create_pie_chart(data)
            else:
                # Default to summary statistics
                fig = create_summary_stats(data)
            
            row_children.append(
                html.Div([
                    dcc.Graph(figure=fig)
                ], style={
                    'width': f"{box['width']}px",
                    'height': f"{box['height']}px",
                    'margin': '10px'
                })
            )
        
        layout_children.append(
            html.Div(row_children, style={
                'display': 'flex',
                'justifyContent': 'space-around',
                'marginBottom': '20px'
            })
        )
    
    app.layout = html.Div(layout_children, style={'padding': '20px'})
    return app

def create_bar_chart(data):
    """Create a sample bar chart"""
    # Implement based on your data
    return go.Figure()

def create_line_chart(data):
    """Create a sample line chart"""
    # Implement based on your data
    return go.Figure()

def create_pie_chart(data):
    """Create a sample pie chart"""
    # Implement based on your data
    return go.Figure()

def create_summary_stats(data):
    """Create summary statistics visualization"""
    # Implement based on your data
    return go.Figure()

def generate_dashboard_from_template(template_image, data, port=8050):
    """Generate a dashboard based on a template image"""
    # Analyze template
    analyzer = DashboardTemplateAnalyzer(template_image)
    template_analysis = analyzer.analyze_template()
    
    # Create dashboard
    app = create_dashboard_from_template(analyzer, template_analysis, data)
    
    # Run dashboard
    app.run_server(debug=True, port=port) 
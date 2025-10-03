import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import json
from datetime import datetime

def create_dashboard(analyzer):
    """Create an interactive dashboard using Dash"""
    app = dash.Dash(__name__)
    
    # Load insights if available
    try:
        with open('insights.json', 'r') as f:
            insights = json.load(f)
    except:
        insights = {'ai_insights': {'summary': 'No insights available'}}
    
    # Create the layout
    app.layout = html.Div([
        # Header
        html.Div([
            html.H1('Data Analysis Dashboard', 
                   style={'textAlign': 'center', 'color': '#2c3e50', 'marginBottom': 30}),
            html.P(f'Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M")}',
                  style={'textAlign': 'center', 'color': '#7f8c8d'})
        ]),
        
        # Dataset Overview
        html.Div([
            html.H2('Dataset Overview', style={'color': '#2c3e50'}),
            html.Div([
                html.Div([
                    html.H3(f'{len(analyzer.data):,}', style={'color': '#3498db'}),
                    html.P('Total Rows')
                ], className='stat-box'),
                html.Div([
                    html.H3(f'{len(analyzer.data.columns):,}', style={'color': '#2ecc71'}),
                    html.P('Total Columns')
                ], className='stat-box'),
                html.Div([
                    html.H3(f'{sum(analyzer.data.isnull().sum()):,}', style={'color': '#e74c3c'}),
                    html.P('Missing Values')
                ], className='stat-box')
            ], style={'display': 'flex', 'justifyContent': 'space-around', 'marginBottom': 30})
        ]),
        
        # Column Type Distribution
        html.Div([
            html.H2('Column Types', style={'color': '#2c3e50'}),
            dcc.Graph(
                figure=px.pie(
                    values=[list(analyzer.column_types.values()).count(t) for t in set(analyzer.column_types.values())],
                    names=list(set(analyzer.column_types.values())),
                    title='Distribution of Column Types'
                )
            )
        ]),
        
        # Interactive Visualizations
        html.Div([
            html.H2('Interactive Visualizations', style={'color': '#2c3e50'}),
            html.Div([
                # Column selector
                html.Div([
                    html.Label('Select Column:'),
                    dcc.Dropdown(
                        id='column-selector',
                        options=[{'label': col, 'value': col} for col in analyzer.data.columns],
                        value=analyzer.data.columns[0]
                    )
                ], style={'width': '30%', 'marginBottom': 20}),
                
                # Visualization container
                html.Div(id='visualization-container')
            ])
        ]),
        
        # Correlation Analysis
        html.Div([
            html.H2('Correlation Analysis', style={'color': '#2c3e50'}),
            dcc.Graph(
                figure=px.imshow(
                    analyzer.data.select_dtypes(include=['float64', 'int64']).corr(),
                    title='Correlation Heatmap',
                    color_continuous_scale='RdBu'
                )
            )
        ]),
        
        # AI Insights
        html.Div([
            html.H2('AI-Powered Insights', style={'color': '#2c3e50'}),
            html.Div([
                html.Pre(
                    insights['ai_insights']['summary'],
                    style={
                        'backgroundColor': '#f8f9fa',
                        'padding': '20px',
                        'borderRadius': '5px',
                        'whiteSpace': 'pre-wrap'
                    }
                )
            ])
        ])
    ], style={'padding': '20px'})
    
    # Callback for interactive visualizations
    @app.callback(
        Output('visualization-container', 'children'),
        Input('column-selector', 'value')
    )
    def update_visualization(selected_column):
        if selected_column is None:
            return html.Div('Please select a column')
        
        col_type = analyzer.column_types[selected_column]
        
        if col_type == 'numerical':
            # Create histogram and box plot
            return html.Div([
                dcc.Graph(
                    figure=px.histogram(
                        analyzer.data,
                        x=selected_column,
                        title=f'Distribution of {selected_column}'
                    )
                ),
                dcc.Graph(
                    figure=px.box(
                        analyzer.data,
                        y=selected_column,
                        title=f'Box Plot of {selected_column}'
                    )
                )
            ])
        
        elif col_type == 'categorical':
            # Create bar chart
            return dcc.Graph(
                figure=px.bar(
                    analyzer.data[selected_column].value_counts(),
                    title=f'Distribution of {selected_column}'
                )
            )
        
        elif col_type == 'date':
            # Create time series plot
            return dcc.Graph(
                figure=px.line(
                    analyzer.data.groupby(selected_column).size().reset_index(),
                    x=selected_column,
                    y=0,
                    title=f'Trend over time for {selected_column}'
                )
            )
    
    return app

def run_dashboard(analyzer, port=8050):
    """Run the dashboard on the specified port"""
    app = create_dashboard(analyzer)
    app.run_server(debug=True, port=port) 
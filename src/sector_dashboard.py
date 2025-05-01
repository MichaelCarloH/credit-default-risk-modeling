import pandas as pd
import plotly.express as px
from dash import dcc, html
from dash.dependencies import Input, Output

def load_sector_data():
    # Load sector data
    sector_data = pd.read_excel("data/output.xlsx")
    return sector_data

def create_sector_layout(app, sector_data):
    # Create layout for the sector dashboard
    app.layout = html.Div([
        html.H1("Sector Overview", style={'textAlign': 'center', 'color': '#4CAF50'}),
        html.Div([
            dcc.Dropdown(
                id='sector-dropdown',
                options=[{'label': sector, 'value': sector} for sector in sector_data['Sector'].unique()],
                placeholder="Select a Sector",
                style={'width': '50%', 'margin': 'auto'}
            ),
            html.Div(id='sector-output-container', style={'marginTop': '20px'})
        ]),
        html.Div([
            dcc.Graph(id='sector-pie-chart'),
            dcc.Graph(id='sector-bar-chart')
        ])
    ])

    # Callbacks for interactivity
    @app.callback(
        [Output('sector-output-container', 'children'),
         Output('sector-pie-chart', 'figure'),
         Output('sector-bar-chart', 'figure')],
        [Input('sector-dropdown', 'value')]
    )
    def update_sector_dashboard(selected_sector):
        if selected_sector:
            filtered_data = sector_data[sector_data['Sector'] == selected_sector]
            pie_chart = px.pie(filtered_data, names='Subsector', values='Value', title=f"{selected_sector} Subsector Distribution")
            bar_chart = px.bar(filtered_data, x='Subsector', y='Value', title=f"{selected_sector} Subsector Values")
            return f"Selected Sector: {selected_sector}", pie_chart, bar_chart
        return "Select a sector to view details.", {}, {}

import pandas as pd
import plotly.express as px
from dash import dcc, html
from dash.dependencies import Input, Output

class SectorDataProcessor:
    def __init__(self, file_path):
        self.file_path = file_path

    def load_data(self):
        # Load the data from the Excel file
        data = pd.read_excel(self.file_path)
        return data

    def calculate_sector_data(self):
        # Extract and calculate sector data from the loaded data
        data = self.load_data()

        # Process the NACE column to group by the first two characters
        data['NACE Sector'] = data['NACE Rev. 2, core code (4 digits)'].astype(str).str[:2]

        # Include company-level information in the sector data
        sector_data = data.groupby(['NACE Sector', 'Company name Latin alphabet']).agg({
            'Operating revenue (Turnover)\nEUR Last avail. yr': 'sum',
            'P/L before tax\nEUR Last avail. yr': 'sum',
            'Number of employees\nLast avail. yr': 'sum',
            'Non-current assets\nEUR Last avail. yr': 'sum',
            'Current assets\nEUR Last avail. yr': 'sum'
        }).reset_index()

        return sector_data


def load_sector_data():
    processor = SectorDataProcessor("data/output.xlsx")
    return processor.calculate_sector_data()


def create_sector_layout(app, sector_data):
    companies = pd.DataFrame({'company': sector_data['Company name Latin alphabet'].unique()})

    app.layout = html.Div([
        html.H1("Sector Dashboard", style={'textAlign': 'center', 'color': '#4CAF50'}),

        # Dropdown for company selection
        html.Div([
            dcc.Dropdown(
                id='company-dropdown',
                options=[{'label': company, 'value': company} for company in companies['company']],
                placeholder="Select a Company",
                style={'width': '50%', 'margin': 'auto'}
            ),
            html.Div(id='company-output-container', style={'marginTop': '20px'})
        ]),

        # Bar chart for sector data
        html.Div([
            dcc.Graph(
                id='sector-bar-chart',
                style={'width': '100%'}
            )
        ]),

        # Output container for sector information
        html.Div(id='output-container', style={'marginTop': '20px'})
    ])

    @app.callback(
        [Output('sector-bar-chart', 'figure'),
         Output('output-container', 'children')],
        [Input('company-dropdown', 'value')]
    )
    def update_sector_dashboard(selected_company):
        if selected_company:
            # Filter data for the selected company
            company_data = sector_data[sector_data['Company name Latin alphabet'] == selected_company]

            if company_data.empty:
                return px.bar(
                    x=['Metric'],
                    y=[0],
                    labels={'x': 'Metric', 'y': 'Value'},
                    title="No Data for Selected Company"
                ), "No data available for the selected company."

            sector_code = company_data['NACE Sector'].values[0]
            sector_info = sector_data[sector_data['NACE Sector'] == sector_code]

            if sector_info.empty:
                return px.bar(
                    x=['Metric'],
                    y=[0],
                    labels={'x': 'Metric', 'y': 'Value'},
                    title=f"No Data for Sector {sector_code}"
                ), "No sector information available for the selected company."

            # Bar chart for sector metrics
            metrics = ['Operating revenue (Turnover)\nEUR Last avail. yr',
                       'P/L before tax\nEUR Last avail. yr',
                       'Number of employees\nLast avail. yr']
            sector_totals = sector_info[metrics].sum()

            bar_chart = px.bar(
                x=metrics,
                y=sector_totals.values,
                labels={'x': 'Metric', 'y': 'Value'},
                title=f"Sector Data for {selected_company} (Sector {sector_code})"
            )

            # Sector details
            sector_details = html.Div([
                html.H3(f"Sector Information for {selected_company}"),
                html.P(f"Sector Code: {sector_code}"),
                html.P(f"Total Operating Revenue: {sector_totals[metrics[0]]:,.2f} EUR"),
                html.P(f"Total Profit/Loss Before Tax: {sector_totals[metrics[1]]:,.2f} EUR"),
                html.P(f"Total Number of Employees: {sector_totals[metrics[2]]:,.0f}")
            ])

            return bar_chart, sector_details

        return px.bar(
            x=['Metric'],
            y=[0],
            labels={'x': 'Metric', 'y': 'Value'},
            title="No Company Selected"
        ), "Select a company to view sector information."

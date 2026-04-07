import pandas as pd
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import llm_research as llm
import json
from sector_dashboard import load_sector_data, create_sector_layout
import plotly.express as px

# Load the companies' data
companies = pd.read_excel("data/output.xlsx")
companies = companies[['Company name Latin alphabet', 'Standardized country']]
companies = companies[companies['Standardized country'] != 'Russia']
companies.columns = ['company', 'country']

companies['company'] = companies['company'].str.title() # Convert company names and country to proper case
companies['country'] = companies['country'].str.title()

# Load sector data
sector_data = load_sector_data()

# Initialize the Dash app
app = dash.Dash(__name__)

# Layout of the app
app.layout = html.Div([
    dcc.Dropdown(
        id='company-dropdown',
        options=[{'label': company, 'value': company} for company in companies['company']],
        placeholder="Company Name"
    ),
    html.Div(id='output-container'),
    dcc.Graph(id='sector-bar-chart')
])

# Callback to update both the sector bar chart and the output container
@app.callback(
    [Output('sector-bar-chart', 'figure'),
     Output('output-container', 'children')],
    [Input('company-dropdown', 'value')]
)
def update_dashboard(selected_company):
    if selected_company:
        # Filter sector data for the selected company
        company_sector_data = sector_data[sector_data['Company name Latin alphabet'] == selected_company]

        if company_sector_data.empty:
            bar_chart = px.bar(
                x=['Metric'],
                y=[0],
                labels={'x': 'Metric', 'y': 'Value'},
                title=f"No Data for {selected_company}"
            )
            return bar_chart, "No sector information available for the selected company."

        # Bar chart for sector metrics
        metrics = ['Operating revenue (Turnover)\nEUR Last avail. yr',
                   'P/L before tax\nEUR Last avail. yr',
                   'Number of employees\nLast avail. yr']
        company_values = company_sector_data[metrics].iloc[0]

        bar_chart = px.bar(
            x=metrics,
            y=company_values.values,
            labels={'x': 'Metric', 'y': 'Value'},
            title=f"Sector Data for {selected_company}"
        )

        # Sector details
        sector_code = company_sector_data['NACE Sector'].iloc[0]
        sector_details = html.Div([
            html.H3(f"Sector Information for {selected_company}"),
            html.P(f"Sector Code: {sector_code}"),
            html.P(f"Operating Revenue: {company_values[0]:,.2f} EUR"),
            html.P(f"Profit/Loss Before Tax: {company_values[1]:,.2f} EUR"),
            html.P(f"Number of Employees: {company_values[2]:,.0f}")
        ])

        return bar_chart, sector_details

    # Default outputs when no company is selected
    return px.bar(
        x=['Metric'],
        y=[0],
        labels={'x': 'Metric', 'y': 'Value'},
        title="No Company Selected"
    ), "Select a company to view sector information."

# Create the sector dashboard layout
create_sector_layout(app, sector_data)

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
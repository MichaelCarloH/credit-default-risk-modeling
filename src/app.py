import pandas as pd
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import llm_research as llm
import json
from sector_dashboard import load_sector_data, create_sector_layout

# Load the companies' data
companies = pd.read_excel("data/output.xlsx")
companies = companies[['Company name Latin alphabet', 'Standardized country']]
companies = companies[companies['Standardized country'] != 'Russia']
companies.columns = ['company', 'country']

companies['company'] = companies['company'].str.title() # Convert company names and country to proper case
companies['country'] = companies['country'].str.title()

# Load sector data
#sector_data = load_sector_data()

# Initialize the Dash app
app = dash.Dash(__name__)

# Layout of the app
app.layout = html.Div([
    dcc.Dropdown(
        id='company-dropdown',
        options=[{'label': company, 'value': company} for company in companies['company']],
        placeholder="Company Name"
    ),
    html.Div(id='output-container')
])

# Callback to update the output container
@app.callback(
    Output('output-container', 'children'),
    [Input('company-dropdown', 'value')]
)
def update_output(selected_company):
    if selected_company:
        company_data = companies[companies['company'] == selected_company].iloc[0]
        country = company_data['country']
        research_data = llm.generate_research(selected_company, country)
        formatted_output = html.Div([
            html.H3("Company Description"),
            html.P(dcc.Markdown(research_data.get("Company Description", "N/A"))),
            html.H3("Financial Description"),
            html.P(dcc.Markdown(research_data.get("Financial Description", "N/A"))),
            html.H3("Potential Benefits"),
            html.P(dcc.Markdown(research_data.get("Potential Benefits", "N/A"))),
            html.H3("Potential Risks"),
            html.P(dcc.Markdown(research_data.get("Potential Risks", "N/A")))
        ])
        return formatted_output
    return "Generate research report by selecting a company from the dropdown."

# Create the sector layout
#create_sector_layout(app, sector_data)

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
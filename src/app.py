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
companies = companies[companies['Standardized country'] != 'Russia']
companies.rename(columns={'Standardized country': 'country', 'Company name Latin alphabet': 'company'}, inplace=True)
companies['company'] = companies['company'].str.title() # Convert company names and country to proper case
companies['country'] = companies['country'].str.title()

# Load sector data
sector_data = load_sector_data()

# Initialize the Dash app
app = dash.Dash(__name__)

# Layout of the app
app.layout = html.Div([
    html.Div([
        # Left side content
        html.Div([
            dcc.Dropdown(
                id='company-dropdown',
                options=[{'label': company, 'value': company} for company in companies['company']],
                placeholder="Company Name",
                style={'width': '600px', 'marginBottom': '10px'}
            ),
            html.Div(id='output-container', style={'maxWidth': '800px', 'fontSize': '12px'}),
            dcc.Graph(id='sector-bar-chart')
        ], style={
            'display': 'flex', 
            'flexDirection': 'column',
            'marginLeft': '20px',
            'marginTop': '20px',
            'width': '50%'
        }),
        
        # Right side content
        html.Div([
            # Big scorecard
            html.Div([
                html.H3('Credit Risk Score', style={'textAlign': 'center', 'marginBottom': '10px', 'fontSize': '16px'}),
                html.Div('85', style={
                    'fontSize': '32px',
                    'textAlign': 'center',
                    'padding': '15px',
                    'backgroundColor': '#f8f9fa',
                    'borderRadius': '8px',
                    'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
                    'marginBottom': '20px'
                })
            ], style={'width': '100%', 'marginBottom': '20px'}),
            
            # P/L row
            html.Div([
                html.Div([
                    html.H3('P/L', style={'textAlign': 'center', 'marginBottom': '10px', 'fontSize': '16px'}),
                    html.Div(id='pl-value', children='Select a company', style={
                        'fontSize': '16px',
                        'textAlign': 'center',
                        'padding': '12px',
                        'backgroundColor': '#f8f9fa',
                        'borderRadius': '8px',
                        'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
                    })
                ], style={'width': '80%', 'marginRight': '10px'}),
                
                html.Div([
                    html.H3('vs. Previous Year', style={'textAlign': 'center', 'marginBottom': '10px', 'fontSize': '16px'}),
                    html.Div(id='pl-change', children='', style={
                        'fontSize': '16px',
                        'textAlign': 'center',
                        'padding': '12px',
                        'backgroundColor': '#f8f9fa',
                        'borderRadius': '8px',
                        'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
                    })
                ], style={'width': '20%'})
            ], style={'display': 'flex', 'flexDirection': 'row', 'width': '100%', 'marginBottom': '20px'}),
            
            # Assets row
            html.Div([
                html.Div([
                    html.H3('Assets', style={'textAlign': 'center', 'marginBottom': '10px', 'fontSize': '16px'}),
                    html.Div('$125M', style={
                        'fontSize': '16px',
                        'textAlign': 'center',
                        'padding': '12px',
                        'backgroundColor': '#f8f9fa',
                        'borderRadius': '8px',
                        'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
                    })
                ], style={'width': '80%', 'marginRight': '10px'}),
                
                html.Div([
                    html.H3('vs. Previous Year', style={'textAlign': 'center', 'marginBottom': '10px', 'fontSize': '16px'}),
                    html.Div('+8%', style={
                        'fontSize': '16px',
                        'textAlign': 'center',
                        'padding': '12px',
                        'backgroundColor': '#f8f9fa',
                        'borderRadius': '8px',
                        'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
                    })
                ], style={'width': '20%'})
            ], style={'display': 'flex', 'flexDirection': 'row', 'width': '100%', 'marginBottom': '20px'}),
            
            # Capital/Debt row 1
            html.Div([
                html.Div([
                    html.H3('Capital', style={'textAlign': 'center', 'marginBottom': '10px', 'fontSize': '16px'}),
                    html.Div('$45M', style={
                        'fontSize': '16px',
                        'textAlign': 'center',
                        'padding': '12px',
                        'backgroundColor': '#f8f9fa',
                        'borderRadius': '8px',
                        'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
                    })
                ], style={'width': '50%', 'marginRight': '10px'}),
                
                html.Div([
                    html.H3('Debt', style={'textAlign': 'center', 'marginBottom': '10px', 'fontSize': '16px'}),
                    html.Div('$30M', style={
                        'fontSize': '16px',
                        'textAlign': 'center',
                        'padding': '12px',
                        'backgroundColor': '#f8f9fa',
                        'borderRadius': '8px',
                        'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
                    })
                ], style={'width': '50%'})
            ], style={'display': 'flex', 'flexDirection': 'row', 'width': '100%', 'marginBottom': '20px'}),
            
            
            # Employees row
            html.Div([
                html.Div([
                    html.H3('Employees', style={'textAlign': 'center', 'marginBottom': '10px', 'fontSize': '16px'}),
                    html.Div('1,250', style={
                        'fontSize': '16px',
                        'textAlign': 'center',
                        'padding': '12px',
                        'backgroundColor': '#f8f9fa',
                        'borderRadius': '8px',
                        'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
                    })
                ], style={'width': '80%', 'marginRight': '10px'}),
                
                html.Div([
                    html.H3('vs. Previous Year', style={'textAlign': 'center', 'marginBottom': '10px', 'fontSize': '16px'}),
                    html.Div('+5%', style={
                        'fontSize': '16px',
                        'textAlign': 'center',
                        'padding': '12px',
                        'backgroundColor': '#f8f9fa',
                        'borderRadius': '8px',
                        'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
                    })
                ], style={'width': '20%'})
            ], style={'display': 'flex', 'flexDirection': 'row', 'width': '100%'})
        ], style={
            'width': '50%',
            'padding': '20px',
            'boxSizing': 'border-box'
        })
    ], style={
        'display': 'flex',
        'flexDirection': 'row',
        'width': '100%',
        'maxWidth': '2000px',
        'margin': '0 auto',
        'fontFamily': 'Avenir, sans-serif'
    })
])

# Callback to update both the sector bar chart and the output container
@app.callback(
    [Output('sector-bar-chart', 'figure'),
     Output('output-container', 'children')],
    [Input('company-dropdown', 'value')]
)
def update_dashboard(selected_company):
    if selected_company:
        company_data = companies[companies['company'] == selected_company].iloc[0]
        country = company_data['country']
        research_data = llm.generate_research(selected_company, country)
        formatted_output = html.Div([
            html.H3("Company Description"),
            dcc.Markdown(research_data.get("Company Description", "N/A")),
            html.H3("Public Financial Description"),
            dcc.Markdown(research_data.get("Public Financial Description", "N/A")),
            html.H3("Potential Benefits"),
            dcc.Markdown(research_data.get("Potential Benefits", "N/A")),
            html.H3("Potential Risks"),
            dcc.Markdown(research_data.get("Potential Risks", "N/A"))
        ])
        company_sector_data = sector_data[sector_data['Company name Latin alphabet'] == selected_company]
        if company_sector_data.empty:
            bar_chart = px.bar(
                x=['Metric'],
                y=[0],
                labels={'x': 'Metric', 'y': 'Value'},
                title=f"No Data for {selected_company}"
            )
        else:
            metrics = [
                'Operating revenue (Turnover)\nEUR Last avail. yr',
                'P/L before tax\nEUR Last avail. yr',
                'Number of employees\nLast avail. yr'
            ]
            company_values = company_sector_data[metrics].iloc[0]
            bar_chart = px.bar(
                x=metrics,
                y=company_values.values,
                labels={'x': 'Metric', 'y': 'Value'},
                title=f"Sector Data for {selected_company}"
            )

        return bar_chart, formatted_output

    return (
        px.bar(
            x=['Metric'],
            y=[0],
            labels={'x': 'Metric', 'y': 'Value'},
            title="No Company Selected"
        ),
        html.P(
            "Generate a research report by selecting a company from the dropdown.",
            style={'color': '#666666', 'fontStyle': 'italic'}
        )
    )

@app.callback(
    Output('pl-value', 'children'),
    [Input('company-dropdown', 'value')]
)
def update_pl_value(selected_company):
    if selected_company:
        company_data = companies[companies['company'] == selected_company].iloc[0]
        pl_value = company_data['P/L before tax\nEUR Last avail. yr']
        if pd.isna(pl_value):
            return 'Not Available'
        # Format the value in thousands with commas
        formatted_pl = f"${int(pl_value):,}"
        return formatted_pl
    return ' '

@app.callback(
    [Output('pl-change', 'children'),
     Output('pl-change', 'style')],
    [Input('company-dropdown', 'value')]
)
def update_pl_change(selected_company):
    base_style = {
        'fontSize': '16px',
        'textAlign': 'center',
        'padding': '12px',
        'backgroundColor': '#f8f9fa',
        'borderRadius': '8px',
        'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
    }
    
    if selected_company:
        company_data = companies[companies['company'] == selected_company].iloc[0]
        pl_change = company_data['P/L for period [=Net income]\nEUR Δ%']
        
        if pd.isna(pl_change):
            return 'N/A', base_style
            
        # Determine color based on thresholds
        if pl_change > 10:
            base_style['color'] = '#008000'  # Green
        elif pl_change < -10:
            base_style['color'] = '#FF0000'  # Red
        else:
            base_style['color'] = '#FFA500'  # Yellow/Orange
            
        return f"{pl_change:+.1f}%", base_style
    return ' ', base_style

# Create the sector dashboard layout
create_sector_layout(app, sector_data)

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
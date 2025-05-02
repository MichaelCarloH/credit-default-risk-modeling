import pandas as pd
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import llm_research as llm

# Load the companies' data
companies = pd.read_csv('./data/output_with_predictions.tsv', sep='\t')
shapley = pd.read_csv('./data/shapley_features.tsv', sep='\t')
# Remove rows with rank 5 from the shapley DataFrame
shapley = shapley[shapley['rank'] != 5]

# Initialize the Dash app
app = dash.Dash(__name__)

# Layout of the app
app.layout = html.Div([
    # Title Card
    html.Div([
        html.H1('RAAD Dashboard', 
            style={
                'textAlign': 'center',
                'fontFamily': 'Avenir, sans-serif',
                'fontSize': '24pt',
                'marginBottom': '5px',
                'fontWeight': 'bold'
            }
        ),
        html.H2([
            'Welcome to the ',
            html.Strong('R'),
            'isk ',
            html.Strong('A'),
            'ssessment from ',
            html.Strong('A'),
            'ugmented ',
            html.Strong('D'),
            'ata Dashboard, an AI-Powered Tool to Model Firms\' Credit Score from Publicly Available Data'
        ],
            style={
                'textAlign': 'center',
                'fontFamily': 'Avenir, sans-serif',
                'fontSize': '14pt',
                'fontWeight': 'normal',
                'color': '#666666',
                'marginTop': '0',
                'marginBottom': '30px'
            }
        )
    ], style={
        'width': '100%',
        'backgroundColor': '#f8f9fa',
        'padding': '20px 0',
        'marginBottom': '20px'
    }),

    # Main content wrapper
    html.Div([
        # Left side content
        html.Div([
            dcc.Dropdown(
                id='company-dropdown',
                options=[
                    {'label': company_name, 'value': company_name} 
                    for company_name in sorted(companies['company_name'])
                ],
                placeholder="Company Name",
                style={'width': '600px', 'marginBottom': '10px'}
            ),
            html.Div(id='output-container', style={'maxWidth': '800px', 'fontSize': '12px'})
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
                html.H3('Credit Score', style={'textAlign': 'center', 'marginBottom': '10px', 'fontSize': '16px'}),
                html.Div(id='credit-score', children='Select a company', style={
                    'fontSize': '24px',
                    'textAlign': 'center',
                    'padding': '15px',
                    'backgroundColor': '#f8f9fa',
                    'borderRadius': '8px',
                    'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
                    'marginBottom': '20px'
                })
            ], style={'width': '100%', 'marginBottom': '20px'}),
            
            # Shapley Values Gauges
            html.Div([
                html.H3('Top Metrics Flagged by Risk Model', style={'textAlign': 'center', 'marginBottom': '5px', 'fontSize': '16px'}),
                html.Div(id='shapley-gauges', style={
                    'display': 'flex', 
                    'flexDirection': 'row', 
                    'flexWrap': 'wrap',
                    'gap': '8px',
                    'justifyContent': 'center',
                    'alignItems': 'center',
                    'marginBottom': '0px'
                })
            ], style={'width': '100%', 'marginBottom': '10px'}),
            
            # Financial Scorecard Header
            html.H3('Financial Scorecard', style={
                'textAlign': 'center',
                'marginTop': '30px',
                'fontSize': '16px',
                'borderTop': '1px solid #ddd',
                'paddingTop': '10px',
                'paddingBottom': '5px'
            }),
            
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
                ], style={'width': '70%', 'marginRight': '10px'}),
                
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
                ], style={'width': '30%'})
            ], style={'display': 'flex', 'flexDirection': 'row', 'width': '100%', 'marginBottom': '10px'}),

            # Operating Revenue and Loans row
            html.Div([
                html.Div([
                    html.H3('Operating Revenue', style={'textAlign': 'center', 'marginBottom': '10px', 'fontSize': '16px'}),
                    html.Div(id='operating-revenue', children='Select a company', style={
                        'fontSize': '16px',
                        'textAlign': 'center',
                        'padding': '12px',
                        'backgroundColor': '#f8f9fa',
                        'borderRadius': '8px',
                        'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
                    })
                ], style={'width': '50%', 'marginRight': '10px'}),
                
                html.Div([
                    html.H3('Loans & Short Term Debt', style={'textAlign': 'center', 'marginBottom': '10px', 'fontSize': '16px'}),
                    html.Div(id='loans', children='Select a company', style={
                        'fontSize': '16px',
                        'textAlign': 'center',
                        'padding': '12px',
                        'backgroundColor': '#f8f9fa',
                        'borderRadius': '8px',
                        'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
                    })
                ], style={'width': '50%'})
            ], style={'display': 'flex', 'flexDirection': 'row', 'width': '100%', 'marginBottom': '10px'}),

            # Current Ratio and Employee Count row
            html.Div([
                html.Div([
                    html.H3('Current Ratio', style={'textAlign': 'center', 'marginBottom': '10px', 'fontSize': '16px'}),
                    html.Div(id='current-ratio', children='Select a company', style={
                        'fontSize': '16px',
                        'textAlign': 'center',
                        'padding': '12px',
                        'backgroundColor': '#f8f9fa',
                        'borderRadius': '8px',
                        'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
                    })
                ], style={'width': '50%', 'marginRight': '10px'}),
                
                html.Div([
                    html.H3('Employee Count', style={'textAlign': 'center', 'marginBottom': '10px', 'fontSize': '16px'}),
                    html.Div(id='employee-count', children='Select a company', style={
                        'fontSize': '16px',
                        'textAlign': 'center',
                        'padding': '12px',
                        'backgroundColor': '#f8f9fa',
                        'borderRadius': '8px',
                        'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
                    })
                ], style={'width': '50%'})
            ], style={'display': 'flex', 'flexDirection': 'row', 'width': '100%', 'marginBottom': '10px'})
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
    }),

    # Combined disclaimers at the bottom
    html.Div([
        html.Div([
            html.P([
                "Disclaimers: ",
                html.Br(),
                "1. This application uses an AI research assistant to gather publicly available company information from the web. The data may be incomplete, outdated, or inaccurate and is provided for general informational purposes only. Users should verify details independently and consult primary sources before making any decisions.",
                html.Br(),
                "2. The credit risk score and associated financial metrics presented herein are derived solely from data available through Moody's Orbis, a third-party financial information platform covering public and private companies. The model relies exclusively on the most recent available annual financial data reported within Orbis, which may be incomplete, outdated, or contain inaccuracies. As such, the credit risk assessment should not be interpreted as definitive. For a more comprehensive and current evaluation of a company's creditworthiness, users are encouraged to obtain detailed, up-to-date financial information directly from the company in question."
            ], style={
                'fontStyle': 'italic',
                'fontSize': '9px',
                'color': '#666666',
                'textAlign': 'justify',
                'margin': '0 auto',
                'maxWidth': '1800px',
                'padding': '0 20px',
                'fontFamily': 'Avenir, sans-serif'
            })
        ])
    ], style={
        'width': '100%',
        'backgroundColor': '#f8f9fa',
        'padding': '15px 0',
        'marginTop': '20px'
    })
])

# Callback to update the output container
@app.callback(
    Output('output-container', 'children'),
    [Input('company-dropdown', 'value')]
)
def update_output(selected_company):
    if selected_company:
        company_data = companies[companies['company_name'] == selected_company].iloc[0]
        country = company_data['country']
        research_data = llm.generate_research(selected_company, country)
        return html.Div([
            html.Div([
                html.H3("Company Description"),
                html.P(dcc.Markdown(research_data.get("Company Description", "I'm sorry. There is no sufficient publicly-available data in the web for this company."))),
                html.H3("Public Financial Description"),
                html.P(dcc.Markdown(research_data.get("Public Financial Description", "I'm sorry. There is no sufficient publicly-available data in the web for this company."))),
                html.H3("Potential Benefits"),
                html.P(dcc.Markdown(research_data.get("Potential Benefits", "I'm sorry. There is no sufficient publicly-available data in the web for this company."))),
                html.H3("Potential Risks"),
                html.P(dcc.Markdown(research_data.get("Potential Risks", "I'm sorry. There is no sufficient publicly-available data in the web for this company.")))
            ])
        ])
    return html.P(
        "Generate a research report by selecting a company from the dropdown. Powered by AI.",
        style={'color': '#666666', 'fontStyle': 'italic'}
    )

@app.callback(
    Output('pl-value', 'children'),
    [Input('company-dropdown', 'value')]
)
def update_pl_value(selected_company):
    if selected_company:
        company_data = companies[companies['company_name'] == selected_company].iloc[0]
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
        company_data = companies[companies['company_name'] == selected_company].iloc[0]
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

# Callback to update the Shapley gauges
@app.callback(
    Output('shapley-gauges', 'children'),
    [Input('company-dropdown', 'value')]
)
def update_shapley_gauges(selected_company):
    if selected_company:
        company_features = shapley[shapley['company_name'] == selected_company]
        if not company_features.empty:
            gauges = []
            for _, row in company_features.iterrows():
                feature = row['feature']
                shap_value = row['shap_value']
                
                def format_title(title, max_line_length=25):  # Increased from 18
                    words = title.split()
                    lines = []
                    current_line = []
                    current_length = 0
                    
                    for word in words:
                        if current_length + len(word) + 1 <= max_line_length:
                            current_line.append(word)
                            current_length += len(word) + 1
                        else:
                            if current_line:
                                lines.append(' '.join(current_line))
                            current_line = [word]
                            current_length = len(word)
                    
                    if current_line:
                        lines.append(' '.join(current_line))
                    
                    return '<br>'.join(lines)

                def get_color(value):
                    if value > 0:
                        return 'rgba(109, 191, 92, 1.0)' 
                    else:
                        return 'rgba(214, 88, 86, 0.5)'
                
                fig = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=shap_value,
                    domain={'x': [0, 1], 'y': [0, 1]},
                    title={
                        'text': format_title(feature),
                        'font': {'size': 8},
                        'align': 'center'
                    },
                    number={'font': {'size': 8}},  # Reduced from 10
                    gauge={
                        'axis': {
                            'range': [-3.5, 3.5],
                            'tickfont': {'size': 6}  # Reduced from 8
                        },
                        'bar': {'color': get_color(shap_value)},
                        'steps': [
                            {'range': [-3.5, 0], 'color': 'rgba(214, 88, 86, 0.5)'},  # Adjusted background opacity
                            {'range': [0, 3.5], 'color': 'rgba(109, 191, 92, 0.5)'}
                        ],
                    }
                ))
                
                fig.update_layout(
                    margin=dict(l=5, r=5, t=20, b=10),  # Reduced bottom margin from 15
                    height=150,  # Reduced from 160
                    width=120,
                    paper_bgcolor='white',
                    plot_bgcolor='white'
                )
                
                gauges.append(html.Div([
                    dcc.Graph(
                        figure=fig,
                        style={
                            'height': '120px',  # Reduced from 160px
                            'width': '150px',
                            'margin': 'auto'
                        },
                        config={'displayModeBar': False}
                    )
                ], style={
                    'flex': '0 0 auto',
                    'minWidth': '120px',
                    'display': 'flex',
                    'justifyContent': 'center',
                    'alignItems': 'center'
                }))
            return gauges
    return []

@app.callback(
    [Output('credit-score', 'children'),
     Output('credit-score', 'style')],
    [Input('company-dropdown', 'value')]
)
def update_credit_score(selected_company):
    base_style = {
        'fontSize': '24px',
        'textAlign': 'center',
        'padding': '15px',
        'backgroundColor': '#f8f9fa',
        'borderRadius': '8px',
        'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
        'marginBottom': '20px'
    }
    
    if selected_company:
        company_data = companies[companies['company_name'] == selected_company].iloc[0]
        score = (1 - company_data['predicted_proba']) * 100
        
        # Add color coding based on the score
        if score >= 80:
            base_style['color'] = '#008000'  # Green for good scores
        elif score >= 60:
            base_style['color'] = '#FFA500'  # Orange for medium scores
        else:
            base_style['color'] = '#FF0000'  # Red for low scores
            
        return f"{score:.1f}", base_style
    return 'Select a company', base_style

# Add these callbacks before the "if __name__ == '__main__':" line
@app.callback(
    Output('operating-revenue', 'children'),
    [Input('company-dropdown', 'value')]
)
def update_operating_revenue(selected_company):
    if selected_company:
        company_data = companies[companies['company_name'] == selected_company].iloc[0]
        revenue = company_data['Operating revenue (Turnover)\nEUR Last avail. yr']
        if pd.isna(revenue):
            return 'Not Available'
        return f"${int(revenue):,}"
    return ''

@app.callback(
    Output('loans', 'children'),
    [Input('company-dropdown', 'value')]
)
def update_loans(selected_company):
    if selected_company:
        company_data = companies[companies['company_name'] == selected_company].iloc[0]
        loans = company_data['Loans & short-term debt\nEUR Last avail. yr'] 
        if pd.isna(loans):
            return 'Not Available'
        return f"${int(loans):,}"
    return ''

@app.callback(
    Output('current-ratio', 'children'),
    [Input('company-dropdown', 'value')]
)
def update_current_ratio(selected_company):
    if selected_company:
        company_data = companies[companies['company_name'] == selected_company].iloc[0]
        ratio = company_data['Current ratio\nLast avail. yr']
        if pd.isna(ratio):
            return 'Not Available'
        return f"{ratio:.2f}"
    return ''

@app.callback(
    Output('employee-count', 'children'),
    [Input('company-dropdown', 'value')]
)
def update_employee_count(selected_company):
    if selected_company:
        company_data = companies[companies['company_name'] == selected_company].iloc[0]
        employees = company_data['Number of employees\nLast avail. yr']
        if pd.isna(employees):
            return 'Not Available'
        return f"{int(employees):,}"
    return ''

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
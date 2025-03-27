# Credit Risk Strategy Brainstorm (27/03/2025)

## Objective  
Create a new credit risk strategy for a bank by analyzing historical data for their credit risk manager.  

## Project Plan  

### Model Probability of Default Curve  
- **Y-axis:** Probability of default  
- **X-axis:** Credit risk ratings  
- Expected to be a **monotone decreasing curve**  

### Key Considerations for a Risk Manager  
- **Probability of Default** → This is what we are computing  
- **Last Given Default**  
- **Exposure at Default**  

## Inputs  

### Financials (from Orbis)  
- Profit/Loss (P/L)  
- Balance Sheet  
- Default flag???  
- Other relevant financial metrics  

### Qualitative Data  
- Industry  
- Sector  
- Country  

### Other Data  
- Age of Company  
- Macroeconomic Factors  

## Scope  
- **Limit to EU companies only** (since we are an EU bank)  

## Modelling  

### Model Selection  
- **Merton Model?** ❌ No, because it requires volatility, etc.  
- **Machine Learning Approach** ✅  
  - Example: **XGBoost** → Outputs probability of default  

### Model Validation  
- Use **default flag** as a validation metric  
- Cross-check with **Orbis default data**  

## Tech Stack  
- **GitHub**  

### Potential Add-On  
- Implement an **LLM to scrape news** and provide a summary of industry sentiment  
  - Ensures the credit risk manager is not relying on a single metric  

---

🚀 **Work in progress – Contributions welcome!**  

from openai import OpenAI
from dotenv import load_dotenv
import json

load_dotenv()
client = OpenAI()

def generate_research(company_name, country):

    prompt = f"""You are a research assistant. You are responsible for researching and providing financial information of the following company. 
    You should always output the following sections: \n\n
    1. Company Description: A short description of the company. The description should include the industry, their main products (if any), and any other relevant information that gives core insight about the company. If possible, use the description of the company seen in the company's website. The description should be concise and informative, written in one paragraph, and contain no more than 250 words. \n
    2. Public Financial Description: Research the company using publicly-available information that may be relevant to the financial status or credit risk of the company. Write a short paragraph of your findings, and always cite your sources. \n
    3. Potential Benefits: Provide a paragraph of the potential upsides of investing in the company. This should include any positive news, developments, or trends that may indicate a positive outlook for the company. \n
    4. Potential Risks: Provide a paragraph of the potential downsides of the company of investing in the company. This should include any negative news, developments, or trends that may indicate a negative outlook for the company. \n

    Always assume that the company is still operating. Assume that you do not have the actual financial info or balance sheet of the company, and that this research is all based on publicly-available information. All output should be in English. Put your answer in JSON format.\n\n

    If you do not have enough information to answer the question, do not make up information. Instead, say "I'm sorry. There is no sufficient publicly-available data in the web for this company."  and do not output a JSON. \n\n
    
    Company name: {company_name}\n 
    Country: {country}\n"""

    response = client.responses.create(
        model="gpt-4.1",
        tools=[{"type": "web_search_preview"}],
        tool_choice="required",
        input=prompt
    )
    # print(response)
    response = response.output_text.replace("json", "").strip()
    response = response.replace("```", "").strip()
    
    try:
        response = json.loads(response)
    except json.JSONDecodeError:
        response = {"error": "Failed to parse JSON response."}
    return response

if __name__ == "__main__":
    company_name = input("Enter the company name: ")
    country = input("Enter the country: ")
    research_report = generate_research(company_name, country)
    print(research_report)
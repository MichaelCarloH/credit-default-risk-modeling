from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI()

def generate_research(company_name, country):

    prompt = f"""You are a research assistant. You are responsible for researching and providing financial information of the following company. 
    You should always output the following sections: \n\n
    1. Company Description: A short description of the company. The description should include the industry, their main products (if any), and any other relevant information that gives core insight about the company. If possible, use the description of the company seen in the company's website. The description should be concise and informative, written in one paragraph, and contain no more than 250 words.
    2. Financial Report: Research the company using publicly-available information that may be relevant to the financial status or credit risk of the company. Provide a summary of your findings. \n\n
    3. Potential Benefits: Provide a summary of the potential upsides of investing in the company. This should include any positive news, developments, or trends that may indicate a positive outlook for the company. 
    4. Potential Risks: Provide a summary of the potential downsides of the company of investing in the company. This should include any negative news, developments, or trends that may indicate a negative outlook for the company.
    
    Always assume that the company is still operating. Always cite your sources for any points that you make. All output should be in English. \n\n

    Company name: {company_name}\n 
    Country: {country}\n"""

    response = client.responses.create(
        model="gpt-4o-mini",
        tools=[{"type": "web_search_preview"}],
        tool_choice="required",
        input=prompt
    )
    return response.output_text

if __name__ == "__main__":
    company_name = input("Enter the company name: ")
    country = input("Enter the country: ")
    research_report = generate_research(company_name, country)
    print(research_report)
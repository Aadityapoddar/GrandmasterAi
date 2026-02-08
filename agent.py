import os
from dotenv import load_dotenv
from google import genai

load_dotenv()


client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def get_ai_solution(problem_data):
    prompt = f"""
    You are a Competitive Programming Grandmaster. 
    Solve this problem with a highly optimized C++ solution.

    TITLE: {problem_data['title']}
    DESCRIPTION: {problem_data['description']}
    CONSTRAINTS: {problem_data['input_spec']}
    
    Briefly explain the logic, then provide the code wrapped in ```cpp tags.
    """

    print("[*] GrandmasterAi Architect is thinking...")
    
    
    response = client.models.generate_content(
        model="gemini-2.5-flash", 
        contents=prompt
    )
    
    return response.text
import re

def extract_code(ai_response):
    """
    Extracts the C++ code block from the AI's Markdown response.
    """
    cpp_pattern = r"```cpp\s*\n?(.*?)\n?```"
    match = re.search(cpp_pattern, ai_response, re.DOTALL | re.IGNORECASE)
    
    if match:
        return match.group(1).strip()
    
    generic_pattern = r"```\s*\n?(.*?)\n?```"
    match = re.search(generic_pattern, ai_response, re.DOTALL)
    
    if match:
        return match.group(1).strip()
    
    return ai_response.strip()
if __name__ == "__main__":
    
    test_data = {
        "title": "Easy Addition",
        "description": "Given two numbers A and B, output their sum.",
        "input_spec": "A and B are integers < 10^9"
    }
    print(extract_code(get_ai_solution(test_data)))
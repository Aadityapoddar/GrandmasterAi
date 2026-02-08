import os
import re
from dotenv import load_dotenv
from google import genai

load_dotenv()


client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def get_ai_solution(problem_data, feedback=None):
    prompt = f"""
    You are a Competitive Programming Grandmaster. 
    Solve this problem with a highly optimized C++ solution.

    TITLE: {problem_data['title']}
    DESCRIPTION: {problem_data['description']}
    CONSTRAINTS: {problem_data['input_spec']}
    
    Briefly explain the logic, then provide the code wrapped in ```cpp tags.
    """
    if feedback:
        prompt += f"\n--- REVISION NEEDED ---\n{feedback}\nFocus on fixing this specific error."
    else:
        prompt += "\nProvide the initial optimized C++ solution."

    print("[*] GrandmasterAi Architect is thinking...")
    
    
    response = client.models.generate_content(
        model="gemini-2.5-flash", 
        contents=prompt
    )
    
    return response.text

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

def get_second_opinion(problem_data, failed_code, error_report):
    prompt = f"""
    You are a Code Reviewer. The following C++ code failed a test case.
    
    PROBLEM: {problem_data['description']}
    FAILED CODE: {failed_code}
    ERROR: {error_report}
    
    Do NOT write code yet. Explain in 3 sentences exactly what logic is missing.
    """
    response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
    return response.text

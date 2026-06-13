import os
import re
from dotenv import load_dotenv
from google import genai
from backend.state import log

load_dotenv()


client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def get_ai_solution(job_id,problem_data, feedback=None, rag_context=None):
    prompt = f"""
    You are a Competitive Programming Grandmaster. 
    Solve this problem with a highly optimized C++ solution.

    TITLE: {problem_data['title']}
    DESCRIPTION: {problem_data['description']}
    CONSTRAINTS: {problem_data['input_spec']}
    
    Briefly explain the logic, then provide the code wrapped in ```cpp tags.
    """
    if rag_context:
        prompt += f"""
    --- SIMILAR PROBLEMS FOR REFERENCE ---
    The following are approaches from similar past problems.
    Use them to guide your thinking, but adapt the logic to THIS problem.

    {rag_context}
    --- END OF REFERENCE ---
    """
    if feedback:
        prompt += f"\n--- REVISION NEEDED ---\n{feedback}\nFocus on fixing this specific error."
    else:
        prompt += "\nProvide the initial optimized C++ solution."

    print("[*] GrandmasterAi Architect is thinking...")
    log(job_id,"GrandmasterAi Architect is thinking...")
    
    
    response = client.models.generate_content(
        model="gemini-2.5-flash", 
        contents=prompt
    )
    
    return response.text

def extract_code(ai_response, language="cpp"):

    pattern = rf"```{language}\s*\n?(.*?)\n?```"
    match = re.search(pattern, ai_response, re.DOTALL | re.IGNORECASE)
    
    if match:
        return match.group(1).strip()
    
    generic_pattern = r"```\s*\n?(.*?)\n?```"
    match = re.search(generic_pattern, ai_response, re.DOTALL)
    
    if match:
        return match.group(1).strip()
    
    return ai_response.strip()

def get_second_opinion(job_id,problem_data, failed_code, error_report):
    prompt = f"""
    You are a Code Reviewer. The following C++ code failed a test case.
    
    PROBLEM: {problem_data['description']}
    FAILED CODE: {failed_code}
    ERROR: {error_report}
    
    Do NOT write the code, just explain in 3 sentences exactly what logic is missing.
    """
    response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
    log(job_id,response.text)
    return response.text

def get_brute_force_solution(problem_data):
    prompt = f"""
    Write a simple, 100% correct Brute Force C++ solution for this problem.
    Ignore time limits ($O(N^2)$ or $O(2^N)$ is fine). 
    Focus ONLY on perfect logic.
    
    PROBLEM: {problem_data['description']}
    """
    response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
    return extract_code(response.text)

def get_test_generator(problem_data):
    prompt = f"""
    Write a Python 3 script that generates ONE random valid test case for this problem.
    Use the 'random' module.
    
    CONSTRAINTS: {problem_data['input_spec']}
    
    Output ONLY the Python code in ```python blocks.
    """
    response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
    return extract_code(response.text, "python")

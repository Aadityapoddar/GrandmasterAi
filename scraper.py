import requests
from bs4 import BeautifulSoup
import re

def scrape_problem(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status() 
    except Exception as e:
        return f"Error fetching URL: {e}"

    soup = BeautifulSoup(response.content, 'html.parser')
    problem_node = soup.find('div', class_='problem-statement')

    description_div = problem_node.find('div', class_='header').find_next_sibling('div')
    description = description_div.get_text(separator="\n").strip()

    
    input_spec = problem_node.find('div', class_='input-specification').get_text(separator="\n").strip()

    
    output_spec = problem_node.find('div', class_='output-specification').get_text(separator="\n").strip()
    # 1. Extract Metadata using the 'Diagnostic' approach
    header = soup.find('div', class_='header')
    
    # Extracting digits and decimals for time 
    time_text = header.find('div', class_='time-limit').text
    time_limit = float(re.search(r"(\d+\.?\d*)", time_text).group(1))

    # Extracting digits for memory
    memory_text = header.find('div', class_='memory-limit').text
    memory_limit = re.search(r"(\d+)", memory_text).group(1) + "m"

    # 2. Extract Sample Test Cases
    samples = []
    inputs = soup.find_all('div', class_='input')
    outputs = soup.find_all('div', class_='output')

    for i, o in zip(inputs, outputs):
        in_data = i.find('pre').get_text(separator="\n").strip()
        out_data = o.find('pre').get_text(separator="\n").strip()
        samples.append({"input": in_data, "output": out_data})

    return {
        "description": description,
        "input_spec": input_spec,
        "output_spec": output_spec,
        "time_limit": time_limit,
        "memory_limit": memory_limit,
        "samples": samples
    }

if __name__ == "__main__":
    url = "https://codeforces.com/problemset/problem/4/A"
    data = scrape_problem(url)
    
    print(f"Time/Memory: {data['time_limit']} / {data['memory_limit']}")
    print(f"\n[DESCRIPTION]\n{data['description'][:200]}...") # Just first 200 chars
    print(f"\n[CONSTRAINTS]\n{data['input_spec']}")
    print(f"\n[SAMPLES] Found {len(data['samples'])} cases.")
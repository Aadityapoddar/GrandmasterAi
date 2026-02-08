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
        "time_limit": time_limit,
        "memory_limit": memory_limit,
        "samples": samples
    }

if __name__ == "__main__":
    # Test with Watermelon (4A)
    test_url = "https://codeforces.com/problemset/problem/4/A"
    data = scrape_problem(test_url)
    
    print(f"--- Metadata ---")
    print(f"Time Limit: {data['time_limit']}s")
    print(f"Memory Limit: {data['memory_limit']}")
    print(f"\n--- Found {len(data['samples'])} Samples ---")
    
    for idx, s in enumerate(data['samples']):
        print(f"Sample {idx+1} Input: {s['input']}")
        print(f"Sample {idx+1} Expected Output: {s['output']}")
        print("-" * 20)
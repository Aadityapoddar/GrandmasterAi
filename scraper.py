import os
import json
import requests
from bs4 import BeautifulSoup
import re

# Ensure a cache directory exists
CACHE_DIR = "cache"
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

session = requests.Session()

def get_cache_path(url):
    """Turns a CF URL into a safe filename: .../4/A -> 4A.json"""
    parts = url.strip("/").split("/")
    # Usually the last two parts are problem ID and Index (e.g., '4', 'A')
    filename = "".join(parts[-2:]) + ".json"
    return os.path.join(CACHE_DIR, filename)

def scrape_problem(url):
    cache_path = get_cache_path(url)

    # 1. Check if we already have this problem cached
    if os.path.exists(cache_path):
        print(f"[*] Cache Hit: Loading {url} from local storage...")
        with open(cache_path, "r") as f:
            return json.load(f)

    # 2. If not cached, scrape it
    print(f"[*] Cache Miss: Fetching {url} from Codeforces...")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        response = session.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # --- (Your existing extraction logic here) ---
        problem_node = soup.find('div', class_='problem-statement')
        header_div = problem_node.find('div', class_='header')
        
        # Metadata
        title = header_div.find('div', class_='title').text.strip()
        time_text = header_div.find('div', class_='time-limit').text
        time_limit = float(re.search(r"(\d+\.?\d*)", time_text).group(1))
        memory_text = header_div.find('div', class_='memory-limit').text
        memory_limit = re.search(r"(\d+)", memory_text).group(1) + "m"
        
        # Description & Specs
        description_div = header_div.find('next_sibling', class_=False) # Simplest next div
        description = problem_node.find('div').find_next_sibling('div').get_text(separator="\n").strip()
        input_spec = problem_node.find('div', class_='input-specification').get_text(separator="\n").strip()
        output_spec = problem_node.find('div', class_='output-specification').get_text(separator="\n").strip()

        # Samples
        samples = []
        inputs = soup.find_all('div', class_='input')
        outputs = soup.find_all('div', class_='output')
        for i, o in zip(inputs, outputs):
            samples.append({
                "input": i.find('pre').get_text(separator="\n").strip(),
                "output": o.find('pre').get_text(separator="\n").strip()
            })

        result = {
            "title": title,
            "description": description,
            "input_spec": input_spec,
            "output_spec": output_spec,
            "time_limit": time_limit,
            "memory_limit": memory_limit,
            "samples": samples
        }

        # 3. Save to Cache
        with open(cache_path, "w") as f:
            json.dump(result, f, indent=4)
        
        return result

    except Exception as e:
        print(f"[!] Error: {e}")
        return None
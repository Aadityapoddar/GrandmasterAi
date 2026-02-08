import os
import json
from curl_cffi import requests
from bs4 import BeautifulSoup
import re
import time
import random

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

    if os.path.exists(cache_path):
        print(f"[*] Cache Hit: Loading {url} from local storage...")
        with open(cache_path, "r") as f:
            return json.load(f)

    
    print(f"[*] Cache Miss: Fetching {url} from Codeforces...")
    user_agents = [
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/118.0'
    ]
    headers = {
        'User-Agent': random.choice(user_agents),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': 'https://codeforces.com/problemset',
        'DNT': '1', # Do Not Track
        'Connection': 'keep-alive',
    }

    print("[*] Mimicking human behavior (pausing)...")
    time.sleep(random.uniform(3, 7))

    try:
        print("[*] Impersonating Chrome to bypass 403...")
        response = requests.get(
            url, 
            impersonate="chrome110", # This is the magic line
            timeout=15
        )
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
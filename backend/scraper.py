import os
import json
from curl_cffi import requests
from bs4 import BeautifulSoup
import re
import time
import random
from backend.state import log

# Ensure a cache directory exists
CACHE_DIR = "cache"
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

session = requests.Session()

def get_cache_path(url):
    parts = url.strip("/").split("/")
    filename = "".join(parts[-2:]) + ".json"
    return os.path.join(CACHE_DIR, filename)

def scrape_problem(job_id,url):
    cache_path = get_cache_path(url)

    if os.path.exists(cache_path):
        print(f"[*] Cache Hit: Loading {url} from local storage")
        log(job_id,"Cache Hit: Loading problem from cache")
        with open(cache_path, "r") as f:
            return json.load(f)

    
    print(f"[*] Cache Miss: Fetching {url} from Codeforces")
    log(job_id,f"Cache Miss: Fetching problem from Codeforces...")

    print("[*] Mimicking human behavior (pausing)")
    time.sleep(random.uniform(3, 7))

    try:
        print("[*] Impersonating Chrome to bypass 403")
        response = requests.get(
            url, 
            impersonate="chrome110",
            timeout=15
        )
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        problem_node = soup.find('div', class_='problem-statement')
        header_div = problem_node.find('div', class_='header')
        
        title = header_div.find('div', class_='title').text.strip()
        time_text = header_div.find('div', class_='time-limit').text
        time_limit = float(re.search(r"(\d+\.?\d*)", time_text).group(1))
        memory_text = header_div.find('div', class_='memory-limit').text
        memory_limit = re.search(r"(\d+)", memory_text).group(1) + "m"
        
        # Description & Specs
        description = problem_node.find('div').find_next_sibling('div').get_text(separator="\n").strip()
        input_spec = problem_node.find('div', class_='input-specification').get_text(separator="\n").strip()
        output_spec = problem_node.find('div', class_='output-specification').get_text(separator="\n").strip()

        # Tags and Rating
        tag_spans = soup.find_all('span', class_='tag-box')
        tags   = []
        rating = None

        for span in tag_spans:
            text = span.get_text(strip=True)
            if span.get('title') == 'Difficulty':
                rating = int(text.replace('*', '').strip())
            else:
                tags.append(text)

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
            "samples": samples,
            "tags": tags, 
            "rating": rating,
        }

        # Save to Cache
        with open(cache_path, "w") as f:
            json.dump(result, f, indent=4)
        
        print(f"✅ Problem fetched: {result['title']}")
        log(job_id,f"✅ Problem fetched: {result['title']}")
        
        return result

    except Exception as e:
        print(f"[!] Error: {e}")
        return None
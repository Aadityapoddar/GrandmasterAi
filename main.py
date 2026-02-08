import sys
from scraper import scrape_problem
from sandbox import run_in_docker

def orchestrate(url, cpp_code):
    # Step 1: Get the 'Eyes' to see the problem
    print(f"[*] Scraping problem data from: {url}")
    data = scrape_problem(url)
    
    if not data or "samples" not in data:
        print("[!] Error: Could not retrieve sample cases.")
        return

    samples = data['samples']
    t_limit = data['time_limit']
    m_limit = data['memory_limit']

    print(f"[*] Problem: {data.get('title', 'Target Found')}")
    print(f"[*] Limits: {t_limit}s / {m_limit}")
    print(f"[*] Found {len(samples)} samples. Starting evaluation...\n")

    passed_count = 0

    # Step 2: Loop through each sample case
    for idx, sample in enumerate(samples):
        input_data = sample['input']
        expected_output = sample['output'].strip()

        print(f"[Test {idx+1}] Running...", end=" ", flush=True)

        # Step 3: Run the code in our 'Vault'
        # We pass the real time/memory limits we just scraped!
        actual_output = run_in_docker(cpp_code, input_data, t_limit, m_limit)

        # Step 4: Verification Logic
        if actual_output == expected_output:
            print("✅ PASSED")
            passed_count += 1
        else:
            print("❌ FAILED")
            print(f"    -- Input --\n{input_data}")
            print(f"    -- Expected --\n{expected_output}")
            print(f"    -- Actual --\n{actual_output}\n")

    # Final Verdict
    print("-" * 30)
    if passed_count == len(samples):
        print(f"OVERALL RESULT: ACCEPTED ({passed_count}/{len(samples)}) 🏆")
    else:
        print(f"OVERALL RESULT: WRONG ANSWER ({passed_count}/{len(samples)})")

if __name__ == "__main__":
    # Test URL: Watermelon (4A)
    target_url = "https://codeforces.com/problemset/problem/4/A"
    
    # Test Code: A solution that handles the '2' case correctly
    test_solution = """
    #include <iostream>
    using namespace std;
    int main() {
        int w; cin >> w;
        if (w > 2 && w % 2 == 0) cout << "YES";
        else cout << "NO";
        return 0;
    }
    """
    
    orchestrate(target_url, test_solution)
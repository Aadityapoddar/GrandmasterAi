import sys
from scraper import scrape_problem
from agent import get_ai_solution, extract_code, get_second_opinion
from sandbox import run_in_docker

def grandmaster_ai_loop(url):
    data = scrape_problem(url)
    raw_response = get_ai_solution(data)
    cpp_code = extract_code(raw_response)

    samples = data['samples']
    current_sample_idx = 0
    max_tries_per_bug = 3
    tries_on_current_bug = 0

    while current_sample_idx < len(samples):
        sample = samples[current_sample_idx]
        print(f"[*] Testing Sample {current_sample_idx + 1}/{len(samples)}...", end=" ", flush=True)

        actual = run_in_docker(cpp_code, sample['input'], data['time_limit'])
        
        if actual.strip() == sample['output'].strip():
            print("✅ PASSED")
            current_sample_idx += 1  
            tries_on_current_bug = 0  
        else:
            tries_on_current_bug += 1
            print(f"❌ FAILED (Try {tries_on_current_bug}/{max_tries_per_bug})")

            if tries_on_current_bug >= max_tries_per_bug:
                print(f"\n[!] Stalled on Sample {current_sample_idx + 1}. Architect couldn't fix it.")
                return False

            
            print(f"[*] Architect is debugging Sample {current_sample_idx + 1}...")
            
            error_report = (
                f"Your previous code failed on a test case.\n"
                f"Input provided: {sample['input']}\n"
                f"Expected Output: {sample['output']}\n"
                f"Your Code's Output: {actual}\n"
                f"PREVIOUS CODE: ```cpp {cpp_code}```\n"
                f"Please fix the logic and provide the full corrected C++ code."
            )
            
            structured_feedback = f"""
            ### EXECUTION FAILURE
            {error_report}

            ### CRITIC'S LOGIC AUDIT
            {get_second_opinion(data, cpp_code, error_report)}

            ### INSTRUCTION
            Address the Critic's points and provide a corrected, full C++ solution.
            """
            # Get new code from the AI
            new_response = get_ai_solution(data, feedback=(structured_feedback))
            cpp_code = extract_code(new_response)

    print("\n🏆 VERDICT: ALL SAMPLES PASSED! Logic is fully verified.")
    print(cpp_code)
    return True
if __name__ == "__main__":
    
    target_url = "https://codeforces.com/problemset/problem/2185/D"
    grandmaster_ai_loop(target_url)
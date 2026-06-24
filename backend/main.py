from backend.scraper import scrape_problem
from backend.agent import get_ai_solution, extract_code, get_second_opinion 
from backend.sandbox import run_in_docker
from backend.state import jobs, log
from backend.retrieve import retrieve_similar_approaches
from backend.stress_test import run_stress_test as _run_stress_test
from backend.stress_test import is_cancelled

def run_pipeline(job_id,url):
    try:
        jobs[job_id]["status"] = "running"
        data = scrape_problem(job_id,url)
        if is_cancelled(job_id): return

        jobs[job_id]["problem_data"] = data
        context=retrieve_similar_approaches(data["description"],data["tags"],data["rating"])
        raw_response = get_ai_solution(job_id,data,None,context)
        log(job_id, "✅ Initial C++ solution generated.")
        cpp_code = extract_code(raw_response)

        cpp_code = sample_test(job_id, data, cpp_code)

        if jobs[job_id]["status"] == "failed":
            return

        print("\n🏆 VERDICT: ALL SAMPLES PASSED!")
        log(job_id,"🏆 VERDICT: ALL SAMPLES PASSED!")
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["result"] = cpp_code

        print(cpp_code)
    except Exception as e:
        if is_cancelled(job_id): return
        log(job_id, f"Unexpected error: {str(e)}")
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)
    return True

def sample_test(job_id,data,cpp_code):
    samples = data['samples']
    current_sample_idx = 0
    max_tries_per_bug = 3
    tries_on_current_bug = 0

    while current_sample_idx < len(samples):
        if is_cancelled(job_id): return cpp_code
        sample = samples[current_sample_idx]
        print(f"[*] Testing Sample {current_sample_idx + 1}/{len(samples)}...", end=" ", flush=True)
        log(job_id,f"Testing Sample {current_sample_idx + 1}/{len(samples)}...")
        actual = run_in_docker(cpp_code, sample['input'], data['time_limit'])
        
        if actual.strip() == sample['output'].strip():
            print("✅ PASSED")
            log(job_id,"✅ PASSED")
            current_sample_idx += 1  
            tries_on_current_bug = 0  
        else:
            tries_on_current_bug += 1
            print(f"❌ FAILED (Try {tries_on_current_bug}/{max_tries_per_bug})")
            log(job_id,f"❌ FAILED (Try {tries_on_current_bug}/{max_tries_per_bug})")

            if tries_on_current_bug >= max_tries_per_bug:
                msg = f"Stalled on Sample {current_sample_idx + 1}. Architect couldn't fix it."
                log(job_id, f"{msg}")
                jobs[job_id]["status"] = "failed"
                jobs[job_id]["error"] = msg
                return False

            
            print(f"[*] Architect is debugging Sample {current_sample_idx + 1}...")
            log(job_id,f"Architect is debugging Sample {current_sample_idx + 1}...")
            
            error_report = (
                f"Your previous code failed on a test case.\n"
                f"Input provided: {sample['input']}\n"
                f"Expected Output: {sample['output']}\n"
                f"Your Code's Output: {actual}\n"
                f"PREVIOUS CODE: ```cpp {cpp_code}```\n"
            )
            
            critic_notes = get_second_opinion(job_id, data, cpp_code, error_report)

            jobs[job_id]["critic_reviews"].append({
                "sample":      current_sample_idx + 1,
                "attempt":     tries_on_current_bug,
                "input":       sample["input"],
                "expected":    sample["output"],
                "got":         actual,
                "review":      critic_notes,
            })
            structured_feedback = f"""
            ### EXECUTION FAILURE
            {error_report}

            ### CRITIC'S LOGIC AUDIT
            {critic_notes}

            ### INSTRUCTION
            Address the Critic's points and provide a corrected, full C++ solution.
            """
            
            new_response = get_ai_solution(job_id,data, feedback=(structured_feedback))
            cpp_code = extract_code(new_response)
    return cpp_code

def run_stress_test(stress_job_id: str, solve_job_id: str, num_tests: int):
    _run_stress_test(stress_job_id, solve_job_id, num_tests)

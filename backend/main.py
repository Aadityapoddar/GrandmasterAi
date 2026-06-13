from backend.scraper import scrape_problem
from backend.agent import get_ai_solution, extract_code, get_second_opinion 
from backend.sandbox import run_in_docker
from backend.state import jobs, log
from backend.retrieve import retrieve_similar_approaches
import subprocess

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
    from backend.agent import get_brute_force_solution, get_test_generator, extract_code, get_ai_solution, get_second_opinion
    from backend.sandbox import run_in_docker
    from backend.state import log

    try:
        jobs[stress_job_id]["status"] = "running"

        solve_job = jobs[solve_job_id]
        cpp_code  = solve_job["result"]
        data      = solve_job["problem_data"]

        log(stress_job_id, "🐢 Generating brute-force solution...")
        brute_code = get_brute_force_solution(data)
        log(stress_job_id, "✅ Brute-force ready.")

        log(stress_job_id, "🎲 Generating random test case generator...")
        generator_code = get_test_generator(data)
        log(stress_job_id, "✅ Generator ready.")

        log(stress_job_id, f"🔁 Running {num_tests} random tests...")

        for i in range(1, num_tests + 1):
            try:
                gen_result = subprocess.run(
                    ["python3", "-c", generator_code],
                    capture_output=True, text=True, timeout=5
                )
                test_input = gen_result.stdout.strip()
            except subprocess.TimeoutExpired:
                log(stress_job_id, f"⚠️  Test {i}: generator timed out, skipping.")
                continue

            if not test_input:
                continue

            fast_out  = run_in_docker(cpp_code,   test_input, data["time_limit"])
            brute_out = run_in_docker(brute_code, test_input, data["time_limit"])

            if fast_out.strip() == brute_out.strip():
                if i % 10 == 0:
                    log(stress_job_id, f"✅ {i}/{num_tests} tests passed...")
                continue

            log(stress_job_id, f"❌ Counterexample found on test {i}!")
            log(stress_job_id, f"📥 Input: {test_input}")
            log(stress_job_id, f"⚡ Got: {fast_out.strip()} | Expected: {brute_out.strip()}")

            data["samples"].append({
                "input":  test_input,
                "output": brute_out.strip()
            })

            log(stress_job_id, "Added the failing test case to the sample test cases for the problem")
            cpp_code=sample_test(stress_job_id,data,cpp_code)

            if jobs[stress_job_id]["status"] == "failed":
                return
            
            jobs[solve_job_id]["result"] = cpp_code

            jobs[stress_job_id]["status"] = "completed"
            jobs[stress_job_id]["result"] = {
                "verdict":      "BUG_FOUND_AND_FIXED",
                "test_number":  i,
                "input":        test_input,
                "fast_output":  fast_out.strip(),
                "brute_output": brute_out.strip(),
            }
            return

        log(stress_job_id, f"🏆 All {num_tests} tests passed!")
        jobs[stress_job_id]["status"] = "completed"
        jobs[stress_job_id]["result"] = {
            "verdict":   "PASSED",
            "tests_run": num_tests,
        }

    except Exception as e:
        log(stress_job_id, f"💥 Stress test error: {str(e)}")
        jobs[stress_job_id]["status"] = "failed"
        jobs[stress_job_id]["error"]  = str(e)

def is_cancelled(job_id: str) -> bool:
    return jobs.get(job_id, {}).get("status") == "cancelled"
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from backend.agent import get_brute_force_solution, get_test_generator
from backend.sandbox import run_in_docker
from backend.state import jobs, log

MAX_WORKERS = 6 


def is_cancelled(job_id: str) -> bool:
    return jobs.get(job_id, {}).get("status") == "cancelled"


def generate_test_inputs(generator_code: str, num_tests: int, stress_job_id: str) -> list[str]:
    test_inputs = []
    for i in range(num_tests):
        try:
            gen_result = subprocess.run(
                ["python3", "-c", generator_code],
                capture_output=True, text=True, timeout=5
            )
            inp = gen_result.stdout.strip()
            if inp:
                test_inputs.append(inp)
        except subprocess.TimeoutExpired:
            log(stress_job_id, f"⚠️  Generator timed out on attempt {i+1}, skipping.")
            continue
    return test_inputs


def run_single_test(test_input: str, cpp_code: str, brute_code: str, time_limit: float) -> dict:
    fast_out  = run_in_docker(cpp_code,   test_input, time_limit)
    brute_out = run_in_docker(brute_code, test_input, time_limit)
    return {
        "passed":    fast_out.strip() == brute_out.strip(),
        "input":     test_input,
        "fast_out":  fast_out.strip(),
        "brute_out": brute_out.strip(),
    }


def run_stress_test(stress_job_id: str, solve_job_id: str, num_tests: int):
    from backend.main import sample_test  

    try:
        jobs[stress_job_id]["status"] = "running"

        solve_job = jobs[solve_job_id]
        cpp_code  = solve_job["result"]
        data      = solve_job["problem_data"]

        # Brute force oracle 
        log(stress_job_id, "🐢 Generating brute-force solution...")
        brute_code = get_brute_force_solution(data)
        log(stress_job_id, "✅ Brute-force ready.")
        if is_cancelled(stress_job_id):
            return

        #  Random test generator
        log(stress_job_id, "🎲 Generating random test case generator...")
        generator_code = get_test_generator(data)
        log(stress_job_id, "✅ Generator ready.")
        if is_cancelled(stress_job_id):
            return

        # Generate all test inputs upfront
        log(stress_job_id, f"🔁 Generating {num_tests} random test cases...")
        test_inputs = generate_test_inputs(generator_code, num_tests, stress_job_id)
        log(stress_job_id, f"✅ Generated {len(test_inputs)} valid test cases.")

        if not test_inputs:
            jobs[stress_job_id]["status"] = "failed"
            jobs[stress_job_id]["error"]  = "Test generator produced no valid inputs."
            return

        # Run tests in parallel
        log(stress_job_id, f"⚙️  Running tests across {MAX_WORKERS} parallel workers...")

        found_bug   = threading.Event()
        bug_result  = {}
        completed   = 0
        lock        = threading.Lock()

        def worker(test_input):
            if found_bug.is_set() or is_cancelled(stress_job_id):
                return None
            result = run_single_test(test_input, cpp_code, brute_code, data["time_limit"])
            if not result["passed"] and not found_bug.is_set():
                found_bug.set()
                bug_result.update(result)
            return result

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {executor.submit(worker, inp): inp for inp in test_inputs}

            for future in as_completed(futures):
                with lock:
                    completed += 1
                    if completed % 10 == 0 and not found_bug.is_set():
                        log(stress_job_id, f"✅ {completed}/{len(test_inputs)} tests completed...")

                if found_bug.is_set():
                    for f in futures:
                        f.cancel()
                    break

                if is_cancelled(stress_job_id):
                    for f in futures:
                        f.cancel()
                    return

        if is_cancelled(stress_job_id):
            return

        if found_bug.is_set():
            log(stress_job_id, f"❌ Counterexample found!")
            log(stress_job_id, f"📥 Input: {bug_result['input']}")
            log(stress_job_id, f"⚡ Got: {bug_result['fast_out']} | Expected: {bug_result['brute_out']}")

            data["samples"].append({
                "input":  bug_result["input"],
                "output": bug_result["brute_out"]
            })

            log(stress_job_id, "Added the failing test case to the sample test cases for the problem")
            cpp_code = sample_test(stress_job_id, data, cpp_code)

            if jobs[stress_job_id]["status"] == "failed":
                return

            jobs[solve_job_id]["result"] = cpp_code

            jobs[stress_job_id]["status"] = "completed"
            jobs[stress_job_id]["result"] = {
                "verdict":      "BUG_FOUND_AND_FIXED",
                "test_number":  completed,
                "input":        bug_result["input"],
                "fast_output":  bug_result["fast_out"],
                "brute_output": bug_result["brute_out"],
            }
            return

        log(stress_job_id, f"🏆 All {len(test_inputs)} tests passed!")
        jobs[stress_job_id]["status"] = "completed"
        jobs[stress_job_id]["result"] = {
            "verdict":   "PASSED",
            "tests_run": len(test_inputs),
        }

    except Exception as e:
        if is_cancelled(stress_job_id):
            return
        log(stress_job_id, f"💥 Stress test error: {str(e)}")
        jobs[stress_job_id]["status"] = "failed"
        jobs[stress_job_id]["error"]  = str(e)
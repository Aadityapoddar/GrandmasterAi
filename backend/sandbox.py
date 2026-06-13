import subprocess
import os

def run_in_docker(cpp_code, input_data, time_limit=1.0, memory_limit="256m"):
    
    with open("temp_sol.cpp", "w") as f:
        f.write(cpp_code)
        f.flush()
        os.fsync(f.fileno())

    docker_cmd = [
        "docker", "run", "--rm",
        "-i", 
        "--memory", memory_limit,        
        "--memory-swap", memory_limit,
        "-v", f"{os.getcwd()}:/home/player",
        "--net", "none",
        "grandmaster-sandbox",
        "sh", "-c", "g++ temp_sol.cpp -o sol && ./sol"
    ]

    try:
        proc = subprocess.run(
            docker_cmd,
            input=input_data,
            text=True,
            capture_output=True,
            timeout=time_limit + 0.5
        )
        
        if proc.returncode == 137:
            return "MLE: Memory Limit Exceeded"
        elif proc.returncode == 139:
            return "Runtime Error: Segmentation Fault (SIGSEGV)"
        elif proc.returncode != 0:
            return f"Runtime Error (Exit Code: {proc.returncode})\nLog: {proc.stderr}"
        return proc.stdout.strip()

    except subprocess.TimeoutExpired:
        return f"TLE: Code exceeded the limit of {time_limit}s"

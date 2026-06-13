from datetime import datetime

jobs: dict[str, dict] = {}

def log(job_id: str, message: str):
    timestamp = datetime.now().strftime("%H:%M:%S")
    jobs[job_id]["logs"].append(f"[{timestamp}] {message}")
    print(f"[{job_id[:8]}] {message}")
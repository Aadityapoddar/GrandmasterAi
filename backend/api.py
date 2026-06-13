import uuid
import asyncio
from fastapi import FastAPI, BackgroundTasks, HTTPException, Path
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, AnyUrl
from backend.main import run_pipeline,run_stress_test
from backend.state import jobs


app = FastAPI(title="GrandmasterAI API", version="1.0.0")


class SolveRequest(BaseModel):
    url: str  

class SolveResponse(BaseModel):
    job_id: str
    message: str

class StressTestRequest(BaseModel):
    job_id:    str
    num_tests: int = 100


@app.post("/solve", response_model=SolveResponse)
def solve(request: SolveRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "status": "queued",
        "logs": [],
        "result": None,
        "error": None,
    }
    background_tasks.add_task(run_pipeline, job_id, request.url)
    return SolveResponse(job_id=job_id, message="Job queued. Use /solve/{job_id}/status to track progress.")

@app.post("/stress-test", response_model=SolveResponse)
def stress_test(request: StressTestRequest, background_tasks: BackgroundTasks):
    if request.job_id not in jobs:
        raise HTTPException(status_code=404, detail="Solve job not found.")

    solve_job = jobs[request.job_id]

    if solve_job["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Solve job is '{solve_job['status']}', not completed. Run /solve first."
        )

    if not solve_job.get("problem_data"):
        raise HTTPException(
            status_code=400,
            detail="No problem data found. Re-run /solve to regenerate."
        )

    if not (1 <= request.num_tests <= 1000):
        raise HTTPException(status_code=400, detail="num_tests must be between 1 and 1000.")

    stress_job_id = str(uuid.uuid4())
    jobs[stress_job_id] = {
        "status":         "queued",
        "logs":           [],
        "result":         None,
        "error":          None,
        "problem_data":   None,
        "critic_reviews": [],
    }

    background_tasks.add_task(run_stress_test, stress_job_id, request.job_id, request.num_tests)

    return SolveResponse(
        job_id=stress_job_id,
        message=f"Stress test queued ({request.num_tests} tests). Poll /solve/{stress_job_id}/status."
    )

@app.get("/solve/{job_id}/status")
def get_status(job_id: str = Path(..., description="Poll this endpoint to check the current job status and all log lines so far.")):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    job = jobs[job_id]
    return {
        "job_id": job_id,
        "status": job["status"],          
        "logs": job["logs"],
        "result": job["result"],           
        "error": job["error"], 
        "critic_reviews": job.get("critic_reviews", []),            
    }


@app.get("/solve/{job_id}/stream")
def stream_logs(job_id: str =Path(...,description='Give job_id to receive logs in real time')):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    async def event_generator():
        sent = 0  
        while True:
            job = jobs[job_id]
            logs = job["logs"]

            while sent < len(logs):
                yield f"data: {logs[sent]}\n\n"
                sent += 1

            if job["status"] in ("completed", "failed"):
                if job["status"] == "completed":
                    # Sending the final solution as a special event
                    result_escaped = job["result"].replace("\n", "\\n")
                    yield f"event: result\ndata: {result_escaped}\n\n"
                else:
                    yield f"event: error\ndata: {job['error']}\n\n"
                yield "event: done\ndata: stream closed\n\n"
                break

            await asyncio.sleep(0.5)  # poll internal state every 500ms

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # important for nginx proxies
        },
    )


@app.get("/health")
def health():
    return {"status": "ok", "active_jobs": len(jobs)}


@app.get("/jobs")
def list_jobs():
    """See all jobs and their statuses (useful during development)."""
    return [
        {"job_id": jid, "status": j["status"]}
        for jid, j in jobs.items()
    ]

@app.post("/solve/{job_id}/cancel")
def cancel_job(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    job = jobs[job_id]
    if job["status"] not in ("queued", "running"):
        raise HTTPException(
            status_code=400,
            detail=f"Job is already '{job['status']}', cannot cancel."
        )
    job["status"] = "cancelled"
    job["error"]  = "Cancelled by user."
    return {"job_id": job_id, "status": "cancelled"}
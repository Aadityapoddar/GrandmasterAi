import { useState, useEffect, useRef } from "react";

const API = "";

export function useJob() {
  const [jobId, setJobId]                 = useState(null);
  const [status, setStatus]               = useState(null);
  const [logs, setLogs]                   = useState([]);
  const [result, setResult]               = useState(null);
  const [error, setError]                 = useState(null);
  const [loading, setLoading]             = useState(false);
  const [criticReviews, setCriticReviews] = useState([]);
  const [solutionCode, setSolutionCode]   = useState(null);  // persists across stress tests
  const pollRef                           = useRef(null);
  const currentJobId                      = useRef(null);

  const stopPolling = () => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  };

  const pollStatus = async (id) => {
    try {
      const res  = await fetch(`${API}/solve/${id}/status`);
      const data = await res.json();

      setStatus(data.status);
      setLogs(data.logs || []);
      if (data.error)          setError(data.error);
      if (data.critic_reviews && data.critic_reviews.length > criticReviews.length) {
        setCriticReviews(data.critic_reviews);
      }

      if (data.result) {
        setResult(data.result);
        // Only update solutionCode when result is actual code (string)
        // Stress test verdicts are objects — don't overwrite the code with them
        if (typeof data.result === "string") {
          setSolutionCode(data.result);
        }
      }

      if (["completed", "failed", "cancelled"].includes(data.status)) {
        stopPolling();
        setLoading(false);
      }
    } catch (e) {
      console.error("Poll error:", e);
    }
  };

  const startJob = (id) => {
    currentJobId.current = id;
    setJobId(id);
    pollRef.current = setInterval(() => pollStatus(id), 1000);
  };

  const submitProblem = async (url) => {
    setLoading(true);
    // Full reset including solutionCode on a new solve
    setLogs([]);
    setResult(null);
    setError(null);
    setCriticReviews([]);
    setSolutionCode(null);
    setStatus("queued");
    stopPolling();

    const res  = await fetch(`${API}/solve`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ url }),
    });
    const data = await res.json();
    startJob(data.job_id);
  };

  const submitStressTest = async (solveJobId, numTests) => {
    setLoading(true);
    // Partial reset — keep solutionCode visible during stress test
    setLogs([]);
    setResult(null);
    setError(null);
    setCriticReviews([]);
    setStatus("queued");
    stopPolling();

    const res  = await fetch(`${API}/stress-test`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ job_id: solveJobId, num_tests: numTests }),
    });
    const data = await res.json();
    startJob(data.job_id);
  };

  const cancelJob = async () => {
    const id = currentJobId.current;
    if (!id) return;
    try {
      await fetch(`${API}/solve/${id}/cancel`, { method: "POST" });
      setStatus("cancelled");
      setLoading(false);
      stopPolling();
    } catch (e) {
      console.error("Cancel error:", e);
    }
  };

  useEffect(() => () => stopPolling(), []);

  return {
    jobId, status, logs, result, error,
    loading, criticReviews, solutionCode,
    submitProblem, submitStressTest, cancelJob,
  };
}
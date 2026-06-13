import { useState, useRef, useEffect } from "react";
import { useJob } from "./hooks/useJob";
import AgentLog from "./components/AgentLog";
import CriticPanel from "./components/CriticPanel";
import CodePanel from "./components/CodePanel";
import styles from "./App.module.css";

export default function App() {
  const [url, setUrl] = useState("");

  const {
    jobId, status, logs, result, error,
    loading, criticReviews, solutionCode,
    submitProblem, submitStressTest, cancelJob,
  } = useJob();

  const [activeSolveJobId, setActiveSolveJobId] = useState(null);

  useEffect(() => {
    if (status === "completed" && jobId && solutionCode) {
      setActiveSolveJobId(jobId); 
    }
  }, [status, jobId, solutionCode]);

  const handleSubmit = async () => {
    if (!url.trim() || loading) return;
    await submitProblem(url.trim());
  };

  const isRunning = status === "running" || status === "queued";

  return (
    <div className={styles.layout}>

      
      <div className={styles.left}>

        
        <div className={styles.brand}>
          <span className={styles.brandIcon}>♟</span>
          <div>
            <div className={styles.brandName}>GrandmasterAI</div>
            <div className={styles.brandSub}>Agentic CP Solver</div>
          </div>
        </div>

        <div className={styles.inputRow}>
          <input
            className={styles.urlInput}
            type="text"
            placeholder="https://codeforces.com/problemset/problem/977/F"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
            disabled={loading}
          />
          {isRunning ? (
            <button className={styles.cancelBtn} onClick={cancelJob}>
              Cancel
            </button>
          ) : (
            <button
              className={styles.solveBtn}
              onClick={handleSubmit}
              disabled={loading || !url.trim()}
            >
              {loading ? <span className={styles.spinner} /> : "Solve"}
            </button>
          )}
        </div>

        {status && (
          <div className={styles.statusRow}>
            <span className={`${styles.statusPill} ${styles[status]}`}>
              {statusLabel(status)}
            </span>
          </div>
        )}

        <div className={styles.logArea}>
          <AgentLog logs={logs} status={status} />
        </div>

        <CriticPanel reviews={criticReviews} />

        {error && status === "failed" && (
          <div className={styles.errorBox}>{error}</div>
        )}

        {status === "cancelled" && (
          <div className={styles.cancelledBox}>Job was cancelled.</div>
        )}

      </div>

      <div className={styles.right}>
        <CodePanel
          solutionCode={solutionCode}
          result={result}
          status={status}
          solveJobId={activeSolveJobId}
          onStressTest={submitStressTest}
        />
      </div>

    </div>
  );
}

function statusLabel(s) {
  return {
    queued:    "Queued",
    running:   "Running…",
    completed: "Completed",
    failed:    "Failed",
    cancelled: "Cancelled",
  }[s] || s;
}
import { useEffect, useRef, useState } from "react";
import styles from "./AgentLog.module.css";

function classifyLine(line) {
  if (line.includes("✅") || line.includes("🏆") || line.includes("PASSED")) return "pass";
  if (line.includes("❌") || line.includes("💥") || line.includes("FAILED"))  return "fail";
  if (line.includes("⚠️"))                                                     return "warn";
  if (line.includes("🔍") || line.includes("🏗️") || line.includes("🧪") ||
      line.includes("🔎") || line.includes("👁️") || line.includes("🐢") ||
      line.includes("🎲") || line.includes("🔁"))                              return "info";
  return "default";
}

export default function AgentLog({ logs, status }) {
  const bodyRef       = useRef(null);
  const bottomRef     = useRef(null);
  const [autoScroll, setAutoScroll] = useState(true);

  // Auto-scroll when new logs arrive — only if user hasn't scrolled up
  useEffect(() => {
    if (autoScroll) {
      bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [logs, autoScroll]);

  // Detect manual scroll — if user scrolls up, disable auto-scroll
  // Re-enable when they scroll back to the bottom
  const handleScroll = () => {
    const el = bodyRef.current;
    if (!el) return;
    const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 40;
    setAutoScroll(atBottom);
  };

  const scrollToBottom = () => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    setAutoScroll(true);
  };

  const isLive = status === "running" || status === "queued";

  return (
    <div className={styles.wrapper}>
      <div className={styles.header}>
        <span className={styles.label}>Agent Log</span>
        <div className={styles.headerRight}>
          {!autoScroll && logs.length > 0 && (
            <button className={styles.scrollBtn} onClick={scrollToBottom}>
              ↓ Latest
            </button>
          )}
          <span className={styles.meta}>
            {isLive && <span className={styles.dot} />}
            {logs.length} lines
          </span>
        </div>
      </div>

      <div className={styles.body} ref={bodyRef} onScroll={handleScroll}>
        {logs.length === 0 ? (
          <span className={styles.empty}>Waiting for pipeline to start…</span>
        ) : (
          logs.map((line, i) => (
            <div key={i} className={`${styles.line} ${styles[classifyLine(line)]}`}>
              {line}
            </div>
          ))
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
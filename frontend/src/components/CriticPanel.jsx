import { useState, memo } from "react";
import styles from "./CriticPanel.module.css";

function CriticPanel({ reviews }) {
  if (!reviews || reviews.length === 0) return null;

  return (
    <div className={styles.wrapper}>
      <div className={styles.header}>
        <span className={styles.icon}>🔍</span>
        <div>
          <div className={styles.title}>Critic Reviews</div>
          <div className={styles.subtitle}>
            What went wrong and why — read these to understand the logic gap
          </div>
        </div>
        <span className={styles.count}>{reviews.length}</span>
      </div>

      <div className={styles.list}>
        {reviews.map((r, i) => (
          <ReviewCard key={i} review={r} index={i} />
        ))}
      </div>
    </div>
  );
}

function ReviewCard({ review, index }) {
  const [open, setOpen] = useState(index === 0); // first one open by default

  return (
    <div className={styles.card}>
      <button className={styles.cardHeader} onClick={() => setOpen((o) => !o)}>
        <div className={styles.cardMeta}>
          <span className={styles.attempt}>
            Sample {review.sample} · Attempt {review.attempt}
          </span>
          <span className={styles.tagFail}>Logic Error</span>
        </div>
        <span className={styles.chevron} data-open={open}>›</span>
      </button>

      {open && (
        <div className={styles.cardBody}>

          {/* ── What went wrong ── */}
          <div className={styles.section}>
            <div className={styles.sectionLabel}>What went wrong</div>
            <div className={styles.diffRow}>
              <div className={styles.diffCol}>
                <span className={styles.diffTag}>Input</span>
                <pre className={styles.diffPre}>{review.input}</pre>
              </div>
              <div className={styles.diffCol}>
                <span className={styles.diffTag + " " + styles.wrong}>Got</span>
                <pre className={styles.diffPre + " " + styles.wrongPre}>{review.got}</pre>
              </div>
              <div className={styles.diffCol}>
                <span className={styles.diffTag + " " + styles.correct}>Expected</span>
                <pre className={styles.diffPre + " " + styles.correctPre}>{review.expected}</pre>
              </div>
            </div>
          </div>

          {/* ── Critic's insight — the learning moment ── */}
          <div className={styles.section}>
            <div className={styles.sectionLabel}>
              <span className={styles.insightDot} />
              Critic's analysis
            </div>
            <div className={styles.insightBox}>
              {review.review.split("\n").filter(Boolean).map((line, i) => (
                <p key={i} className={styles.insightLine}>{line}</p>
              ))}
            </div>
          </div>

        </div>
      )}
    </div>
  );
}
export default memo(CriticPanel);

import { useState } from "react";
import styles from "./CodePanel.module.css";

export default function CodePanel({ solutionCode, result, status, onStressTest, solveJobId }) {
  const [numTests, setNumTests] = useState(100);
  const [copied, setCopied]     = useState(false);

  const isStressResult = result && typeof result === "object";
  const isEmpty        = !solutionCode;

  const copyCode = () => {
    navigator.clipboard.writeText(solutionCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <div className={styles.wrapper}>

      {/* ── Header ── */}
      <div className={styles.header}>
        <span className={styles.label}>Solution</span>
        {solutionCode && (
          <button className={styles.copyBtn} onClick={copyCode}>
            {copied ? "✓ Copied" : "Copy"}
          </button>
        )}
      </div>

      {/* ── Code area ── */}
      <div className={styles.codeArea}>
        {isEmpty ? (
          <div className={styles.empty}>
            <span className={styles.emptyIcon}>♟</span>
            <span>Solution will appear here once generated.</span>
          </div>
        ) : (
          <pre className={styles.code}>{solutionCode}</pre>
        )}
      </div>

      {/* ── Stress test controls ── */}
      {solutionCode && (
        <div className={styles.footer}>

          {/* Stress verdict */}
          {isStressResult && (
            <div className={styles.verdict}>
              {result.verdict === "PASSED" && (
                <span className={styles.badge + " " + styles.success}>
                  ✓ {result.tests_run} stress tests passed
                </span>
              )}
              {result.verdict === "BUG_FOUND_AND_FIXED" && (
                <>
                  <span className={styles.badge + " " + styles.warning}>
                    ⚠ Bug found on test #{result.test_number} — fixed
                  </span>
                  <DiffGrid
                    input={result.input}
                    got={result.fast_output}
                    expected={result.brute_output}
                    styles={styles}
                  />
                </>
              )}
              {result.verdict === "BUG_FOUND" && (
                <>
                  <span className={styles.badge + " " + styles.danger}>
                    ✗ Bug found on test #{result.test_number} — could not fix
                  </span>
                  <DiffGrid
                    input={result.input}
                    got={result.fast_output}
                    expected={result.brute_output}
                    styles={styles}
                  />
                </>
              )}
            </div>
          )}

          {/* Stress test row */}
          {solveJobId && (
            <div className={styles.stressRow}>
              <span className={styles.stressLabel}>
                {isStressResult ? "Run again?" : "Stress test?"}
              </span>
              <input
                type="number"
                className={styles.numInput}
                value={numTests}
                min={10}
                max={1000}
                onChange={(e) => setNumTests(Number(e.target.value))}
              />
              <span className={styles.stressHint}>tests</span>
              <button
                className={styles.stressBtn}
                onClick={() => onStressTest(solveJobId, numTests)}
              >
                Run
              </button>
            </div>
          )}

        </div>
      )}

    </div>
  );
}

function DiffGrid({ input, got, expected, styles }) {
  return (
    <div className={styles.diffGrid}>
      <div className={styles.diffBlock}>
        <span className={styles.diffLabel}>Input</span>
        <pre className={styles.diffPre}>{input}</pre>
      </div>
      <div className={styles.diffBlock}>
        <span className={styles.diffLabel}>Got</span>
        <pre className={styles.diffPre + " " + styles.wrong}>{got}</pre>
      </div>
      <div className={styles.diffBlock}>
        <span className={styles.diffLabel}>Expected</span>
        <pre className={styles.diffPre + " " + styles.correct}>{expected}</pre>
      </div>
    </div>
  );
}
# 🏆 GrandmasterAi: An Agentic Framework for Algorithmic Verification

**GrandmasterAi** is an advanced, multi-agent AI system designed to serve as an automated "Peer Reviewer" for Competitive Programming (CP) and complex algorithmic development. By simulating the workflow of a high-level software engineer—from requirement analysis to rigorous differential testing—the system helps developers identify subtle logic flaws and optimize implementations through autonomous, localized feedback loops.

---

## 🤖 The Multi-Agent Architecture

The power of GrandmasterAi lies in its collaborative "Brain," composed of specialized LLM-based agents that debate, audit, and refine code in real-time.



### 1. The Eyes (Scraper Agent)
Utilizing `curl_cffi` and `BeautifulSoup4`, this agent ingests problem statements, constraints, and official sample cases from platforms like Codeforces. It translates raw HTML into structured JSON metadata for the downstream agents.

### 2. The Architect (Optimizer Agent)
The primary coder. It focuses on time and space complexity ($O(N \log N)$, $O(N)$, etc.), translating high-level algorithmic logic into production-grade C++ code. It uses feedback from other agents to perform surgical refinements.

### 3. The Critic (Auditor Agent)
A "second-opinion" specialist. When a solution fails a test case, the Critic performs a root-cause analysis. It identifies logic gaps, integer overflows, or off-by-one errors and provides a technical brief to the Architect for the next iteration.

### 4. The Oracle (Brute Force Agent)
To ensure mathematical truth, the Oracle generates a simple, $100\%$ correct brute-force solution. It ignores time limits to focus purely on the correct logic of the problem, serving as the "Source of Truth" for differential testing.

### 5. The Stressor (Test Generator Agent)
A dynamic scriptwriter that generates random, constraint-compliant test cases. It targets potential edge cases that basic problem samples often miss, ensuring the solution is robust beyond the provided examples.

---

## 🛠️ The Verification Workflow

GrandmasterAi doesn't just "guess" code; it proves its validity through a rigorous five-stage pipeline:

1.  **Ingestion:** Problem data is scraped, parsed, and structured.
2.  **Initial Synthesis:** The Architect generates the first optimized candidate based on the parsed constraints.
3.  **Warden Phase:** The solution is executed inside a **Dockerized Sandbox** against official samples to check basic correctness.
4.  **Refinement Loop:** If samples fail, the Critic audits the failure and the Architect rewrites the code with the previous failure as context.
5.  **Autonomous Stress Testing:** The system enters a **Differential Duel**. The Optimized Code and the Brute Force Oracle are run against random inputs. If they diverge, the system self-corrects using the failure as feedback.

---

## 💻 Tech Stack

| Component | Technology |
| :--- | :--- |
| **LLM** | Google Gemini 1.5 Flash |
| **Frontend** | Streamlit (Reactive UI) |
| **Sandbox** | Docker (Isolated C++ Execution) |
| **Scraping** | `curl_cffi` & `BeautifulSoup4` |
| **Languages** | Python 3.13 (Orchestration) & C++17/20 (Solutions) |

---

## 🎯 Project Goals

Developed as a "Proof of Work" for high-level software engineering, **GrandmasterAi** demonstrates the potential of Agentic AI in solving complex, logic-heavy tasks. It serves as a tool for competitive programmers to:
* Verify logic against a brute-force baseline.
* Automatically discover subtle edge cases.
* Explore highly optimized implementations of complex algorithms.


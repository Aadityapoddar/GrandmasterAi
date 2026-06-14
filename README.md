<div align="center">

# ♟ GrandmasterAI

### A Competitive Programming Learning Assistant powered by Multi-Agent AI and RAG

</div>

---

## What is this?

Getting stuck on a competitive programming problem is frustrating. But the real problem is not being stuck, it is not knowing *why* you are stuck or *what kind of thinking* unlocks it.

GrandmasterAI is a learning tool built around that gap. The idea was simple use a RAG pipeline over competitive programming editorials to show a learner *how experienced problem-solvers approach similar problems* and then walk them through the full reasoning chain, step by step, with every decision visible.

It retrieves problems with similar approaches from its knowledge base, shows you those approaches, builds a solution from that reasoning, verifies it, and when it fails it explains exactly what was logically wrong before trying to fix it. The goal at every stage is the same **help the user understand the thinking.**

The retrieved problems, the approach reasoning, the failure analysis, the fix all of it is surfaced directly in the UI so a learner can follow along and actually absorb something.

---

## The Learning Loop

```
New problem submitted
    │
    ▼
Retrieve similar past problems from 3,500+ editorials (of probelm rating 1200-2000)
    → Shows the user: "problems like this used these techniques"
    │
    ▼
Build an approach from that retrieved knowledge
    → Shows the user: "here is the reasoning behind the solution"
    │
    ▼
Implement and verify against sample test cases (sandboxed)
    → Shows the user: which samples pass and which fail
    │
    ▼
If it fails Critic explains the logic gap in plain language
    → Shows the user: "here is exactly what was wrong and why"
    │
    ▼
Architect fixes based on Critic's analysis
    → Shows the user: the revised solution and what changed
    │
    ▼
Stress test against hundreds of random cases (optional)
    → Shows the user: edge cases that samples missed, and why
```

Every step produces something the user can read, not just a silent state transition.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     User Interface (React)                      │
│   Left: Agent Log + Critic Review Cards                         │
│   Right: C++ Solution Panel + Stress Test Controls              │
└──────────────────────┬──────────────────────────────────────────┘
                       │ POST /solve
┌──────────────────────▼──────────────────────────────────────────┐
│                     FastAPI Backend                             │
│              (async job queue, SSE streaming)                   │
└──┬───────────────────┬─────────────────────┬────────────────────┘
   │                   │                     │
   ▼                   ▼                     ▼
┌──────────┐    ┌─────────────┐    ┌─────────────────────┐
│ Scraper  │    │  RAG Engine │    │   Agent Pipeline    │
│          │    │             │    │                     │
│ Problem  │    │ HyDE hint   │    │ Architect           │
│ statement│    │ → embed     │    │   approach → code   │
│ tags     │    │ → search    │    │                     │
│ rating   │    │ → top-3     │    │ Sample Verifier     │
│ samples  │    │   editorials│    │   Docker sandbox    │
└──────────┘    └──────┬──────┘    │                     │
                       │           │ Critic              │
                ┌──────▼──────┐    │   explains failure  │
                │   Qdrant    │    │                     │
                │  3,500+     │    │ Stress Tester       │
                │  editorial  │    │   differential      │
                │  embeddings │    │   testing           │
                └─────────────┘    └─────────────────────┘
```

---

## Key Engineering Decisions

### 1. HyDE for semantic retrieval
Problem statements and editorials use completely different vocabulary. A problem says "given an array of N integers" an editorial says "this suggests a DP approach with bitmask states." Embedding them in the same space and searching directly gives poor results.

The fix: before searching, ask the LLM to write a short hypothetical editorial hint for the problem. Embed *that* and search against the stored editorials. You're now comparing editorial-language to editorial-language. In practice this gave 0.80+ similarity scores on genuinely technique-analogous problems.

### 2. Critic constrained to 3 sentences, no code
If the Critic just rewrote the code, the user learns nothing. It is explicitly prompted to produce exactly 3 sentences of plain-language reasoning with no code forcing it to name the conceptual gap. That explanation is the actual learning artifact, surfaced as a card in the UI.

### 3. Editorial chunking as problem-approach pairs
Each editorial is stored as a combined chunk: the problem statement followed by the tutorial explanation. The reason is that the statement tells the model what kind of problem this technique applies to, and the tutorial tells it how the technique works. Storing them together means when a new problem comes in, the retrieval finds editorials that match on both — not just technique similarity, but also problem structure similarity.

### 4. Differential testing for stress testing
The stress tester generates a brute-force reference solution and a random test case generator via the LLM, then compares both solutions across hundreds of random inputs. When outputs differ, a counterexample is found automatically no manual edge case writing needed. This is the same technique used in production software testing and it teaches edge case thinking in a concrete, visible way.

### 5. Sandboxed code execution
All generated C++ runs inside an isolated Docker container with strict time limits. The host filesystem is never touched.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| LLM | Gemini 2.5 Flash |
| Embeddings | gemini-embedding-2 (3072 dimensions) |
| Vector Database | Qdrant |
| Backend | FastAPI + Python 3.13 |
| Frontend | React 18 + Vite |
| Code Execution | Docker (sandboxed) |
| Editorial Dataset | CREST — 3,546 Codeforces problems (rated 1200–2000) |

---

## Project Structure

```
GrandmasterAI/
├── backend/
│   ├── agent.py        
│   ├── api.py          
│   ├── ingest.py       
│   ├── main.py         
│   ├── retrieve.py     
│   ├── sandbox.py      
│   ├── scraper.py      
│   └── state.py        
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── AgentLog.jsx      
│   │   │   ├── CodePanel.jsx     
│   │   │   └── CriticPanel.jsx   
│   │   ├── hooks/
│   │   │   └── useJob.js         
│   │   └── App.jsx               
│   └── vite.config.js
├── cache/
├── .env
├── Dockerfile
└── requirements.txt
```

---

## Setup

### Prerequisites
- Python 3.13+
- Docker
- Node.js 18+
- Gemini API key ([get one here](https://aistudio.google.com/apikey))

### 1. Start Qdrant

```bash
docker run -p 6333:6333 -v qdrant_storage:/qdrant/storage qdrant/qdrant
```

### 2. Clone and install

```bash
git clone https://github.com/Aadityapoddar/GrandmasterAi
cd GrandmasterAi
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
# Add your GEMINI_API_KEY to .env
```

### 4. Ingest the editorial knowledge base

```bash
python backend/ingest.py
# ~30 minutes on first run, resumable if interrupted
```

### 5. Start the backend

```bash
cd backend
python -m uvicorn api:app --reload
```

### 6. Start the frontend

```bash
cd frontend
npm install && npm run dev
```

Open `http://localhost:3000`.

---

## Using the Tool

1. Paste a Codeforces problem URL and click Solve
2. Watch the agent log, see which similar problems were retrieved and what techniques they used
3. If the solution fails, read the Critic cards they explain the logic gap, not just patch the code
4. See the verified solution from the right panel
5. Optionally run a stress test to surface edge cases the sample inputs missed

---

## Motivation

I wanted to explore whether a RAG pipeline could be used to build something genuinely useful for learning, a system that makes the reasoning behind competitive programming visible. Competitive programming felt like a good domain for this as problems have objective correctness criteria, and there is a rich ecosystem of editorials to build a knowledge base from.


---

<div align="center">
Built by <a href="https://github.com/Aadityapoddar">Aaditya Poddar</a>
</div>

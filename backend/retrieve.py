import os
from dotenv import load_dotenv
from google import genai
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchAny

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
QDRANT_URL     = "http://localhost:6333"
COLLECTION     = "cp_editorials"
EMBED_MODEL    = "gemini-embedding-2"
TOP_K          = 3   

client = genai.Client(api_key=GEMINI_API_KEY)
qdrant = QdrantClient(url=QDRANT_URL)


def generate_hyde_hint(problem_statement: str) -> str:
    prompt = f"""You are a competitive programming expert.
Given this problem, write a SHORT 3-4 sentence editorial hint describing:
1. The key observation that unlocks the solution
2. The algorithmic technique or approach to use
3. Why this technique fits (what constraint/pattern signals it)

Write in general technique terms, not problem-specific variable names.
Do NOT write any code. Do NOT solve the full problem.

PROBLEM:
{problem_statement[:2000]}

Editorial hint:"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    return response.text.strip()


# Embed the HyDE hint 
def embed_query(text: str) -> list[float]:
    prefixed = f"Find competitive programming editorials with similar approach to: {text}"
    result   = client.models.embed_content(
        model=EMBED_MODEL,
        contents=prefixed,
    )
    return result.embeddings[0].values


# Search Qdrant 
def search_similar(query_vector: list[float], tags: list[str] = None, rating: int = None) -> list[dict]:
    
    search_filter = None
    if tags:
        search_filter = Filter(
            must=[FieldCondition(key="tags", match=MatchAny(any=tags))]
        )

    results = qdrant.query_points(
        collection_name=COLLECTION,
        query=query_vector,
        query_filter=search_filter,
        limit=TOP_K,
        with_payload=True,
        score_threshold=0.5,
    ).points


    if len(results) < 2 and tags:
        results = qdrant.query_points(
            collection_name=COLLECTION,
            query=query_vector,
            limit=TOP_K,
            with_payload=True,
            score_threshold=0.5,
        ).points

    return results


# Format for prompt injection 

def format_for_prompt(results: list) -> str:
    if not results:
        return ""

    sections = []
    for i, result in enumerate(results, 1):
        payload = result.payload
        section = f"""--- Similar Problem {i} ---
Title:      {payload['title']} ({payload['url']})
Tags:       {', '.join(payload['tags'])}
Difficulty: {payload['rating']}
Similarity: {result.score:.2f}

Approach:
{payload['tutorial']}
"""
        sections.append(section)

    return "\n".join(sections)


# Main retrieval function 

def retrieve_similar_approaches(
    problem_statement: str,
    tags: list[str] = None,
    rating: int = None
) -> str:
    """
    Full RAG pipeline: HyDE → embed → search → format.
    Returns a formatted string ready to inject into the Architect's prompt.
    Returns empty string if nothing relevant found.
    """

    hyde_hint = generate_hyde_hint(problem_statement)
    print(f"\n🔍 HyDE hint generated:\n{hyde_hint}\n")

    query_vector = embed_query(hyde_hint)

    results = search_similar(query_vector, tags=tags, rating=rating)

    if not results:
        print("⚠️  No similar problems found above similarity threshold.")
        return ""

    print(f"✅ Retrieved {len(results)} similar problems:")
    for r in results:
        print(f"   - {r.payload['title']} (similarity: {r.score:.2f})")

    return format_for_prompt(results)

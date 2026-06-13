import os
import time
import json
from datasets import load_dataset
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchAny
from google import genai
from google.genai import types
from dotenv import load_dotenv

GEMINI_API_KEY  = os.getenv("GEMINI_API_KEY")
QDRANT_URL      = "http://localhost:6333"
COLLECTION      = "cp_editorials"
EMBED_MODEL = "gemini-embedding-2"
VECTOR_DIM  = 3072
CHECKPOINT_FILE = "ingested_ids.json"   

MIN_RATING = 1200
MAX_RATING = 2000

load_dotenv()

client = genai.Client(api_key=GEMINI_API_KEY)
qdrant = QdrantClient(url=QDRANT_URL)


def load_checkpoint() -> set:
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE) as f:
            return set(json.load(f))
    return set()

def save_checkpoint(processed: set):
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump(list(processed), f)


# Qdrant setup 
def setup_collection():
    existing = [c.name for c in qdrant.get_collections().collections]
    if COLLECTION in existing:
        count = qdrant.count(collection_name=COLLECTION).count
        print(f"✅ Collection '{COLLECTION}' already exists ({count} vectors).")
        return
    qdrant.create_collection(
        collection_name=COLLECTION,
        vectors_config=VectorParams(size=VECTOR_DIM, distance=Distance.COSINE)
    )
    print(f"✅ Collection '{COLLECTION}' created.")


# Embed 
def embed(text: str, is_query: bool = False) -> list[float]:
    if is_query:
        prefixed = f"Find competitive programming editorials with similar approach to: {text}"
    else:
        prefixed = f"Competitive programming editorial: {text}"
    
    result = client.models.embed_content(
        model=EMBED_MODEL,
        contents=prefixed,
    )
    return result.embeddings[0].values


def build_embed_text(statement: str, tutorial: str) -> str:
    statement = statement[:1500].strip()
    tutorial  = tutorial[:1500].strip()
    return f"PROBLEM:\n{statement}\n\nAPPROACH:\n{tutorial}"


# Store 

def store_problem(problem_id: str, embed_text: str, payload: dict):
    vector = embed(embed_text)
    point  = PointStruct(
        id      = abs(hash(problem_id)) % (2**63),
        vector  = vector,
        payload = payload       
    )
    qdrant.upsert(collection_name=COLLECTION, points=[point])


def main():
    print("Loading CREST dataset from Hugging Face...")
    ds = load_dataset("ZaniteA/crest-codeforces-annotated-problems", split="train")
    print(f"   Total problems in dataset: {len(ds)}")

    
    filtered = [
        row for row in ds
        if row["tutorial"]                              
        and row["rating"]                               
        and MIN_RATING <= row["rating"] <= MAX_RATING   
    ]
    print(f"   Problems after filtering ({MIN_RATING}–{MAX_RATING}, has tutorial): {len(filtered)}")

    setup_collection()
    processed = load_checkpoint()
    print(f"   Already processed (from checkpoint): {len(processed)}\n")

    ingested = 0
    skipped  = 0

    for i, row in enumerate(filtered):
        problem_id = f"{row['contest_id']}{row['index']}" 

        if problem_id in processed:
            skipped += 1
            continue

        try:
            embed_text = build_embed_text(row["statement"], row["tutorial"])

            payload = {
                "problem_id": problem_id,
                "title":      row["title"],
                "tags":       row["tags"],
                "rating":     row["rating"],
                "tutorial":   row["tutorial"][:2000],  
                "statement":  row["statement"][:1000], 
                "url":        f"https://codeforces.com/problemset/problem/{row['contest_id']}/{row['index']}"
            }

            store_problem(problem_id, embed_text, payload)

            processed.add(problem_id)
            ingested += 1

            if ingested % 10 == 0:
                save_checkpoint(processed)
                print(f"   ✅ {ingested} ingested, {i+1}/{len(filtered)} processed — last: {problem_id} ({row['title']})")

            time.sleep(0.05)

        except Exception as e:
            print(f"   ❌ Failed on {problem_id}: {e}")
            time.sleep(2)  
            continue

    save_checkpoint(processed)

    total = qdrant.count(collection_name=COLLECTION).count
    print(f"\n✅ Done! Ingested: {ingested} | Skipped (already done): {skipped}")
    print(f"   Total vectors in Qdrant: {total}")


if __name__ == "__main__":
    main()
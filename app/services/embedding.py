import voyageai
from app.config import settings
from app.db.vectordb import (
    get_chroma_client,
    get_raw_contents_collection,
    get_contents_collection,
)
from app.db.supabase_client import get_supabase

voyage_client = voyageai.Client(api_key=settings.voyage_api_key)


def embed_raw_content(
    raw_content_id: int, text: str, category: str, tags: list[str]
) -> str:
    """글감 1개를 임베딩해서 ChromaDB에 저장. embedding_id 반환."""
    result = voyage_client.embed([text], model="voyage-3")
    embedding = result.embeddings[0]

    client = get_chroma_client()
    collection = get_raw_contents_collection(client)

    doc_id = str(raw_content_id)

    collection.upsert(
        ids=[doc_id],
        embeddings=[embedding],
        documents=[text],
        metadatas=[
            {
                "raw_content_id": raw_content_id,
                "category": category,
                "tags": ", ".join(tags),
            }
        ],
    )

    return doc_id


def embed_all_raw_contents() -> int:
    """Supabase의 글감 전체를 ChromaDB에 임베딩 저장. 저장된 개수 반환."""
    supabase = get_supabase()
    rows = (
        supabase.table("raw_contents")
        .select("id, text, category_id, tags, categories(category_name)")
        .execute()
        .data
    )

    BATCH_SIZE = 20
    client = get_chroma_client()
    collection = get_raw_contents_collection(client)

    for i in range(0, len(rows), BATCH_SIZE):
        batch = rows[i : i + BATCH_SIZE]
        texts = [row["text"] for row in batch]

        result = voyage_client.embed(texts, model="voyage-3")

        ids = [str(row["id"]) for row in batch]
        embeddings = result.embeddings
        documents = texts
        metadatas = [
            {
                "raw_content_id": row["id"],
                "category": (
                    row.get("categories", {}).get("category_name", "")
                    if row.get("categories")
                    else ""
                ),
                "tags": ", ".join(row.get("tags") or []),
            }
            for row in batch
        ]

        collection.upsert(
            ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas
        )

    return len(rows)


def search_raw_contents(query: str, n_results: int = 5) -> list[dict]:
    """쿼리와 유사한 글감을 ChromaDB에서 검색. 결과 리스트 반환."""
    result = voyage_client.embed([query], model="voyage-3")
    query_embedding = result.embeddings[0]

    client = get_chroma_client()
    collection = get_raw_contents_collection(client)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )

    output = []
    for i in range(len(results["ids"][0])):
        output.append(
            {
                "raw_content_id": results["metadatas"][0][i]["raw_content_id"],
                "text": results["documents"][0][i],
                "category": results["metadatas"][0][i]["category"],
                "tags": results["metadatas"][0][i]["tags"],
                "distance": results["distances"][0][i],
            }
        )

    return output


def embed_content(content_id: str, text: str, topic: str, tags: list[str]) -> str:
    """글감 1개를 임베딩해서 ChromaDB에 저장. embedding_id 반환."""
    result = voyage_client.embed([text], model="voyage-3")
    embedding = result.embeddings[0]

    client = get_chroma_client()
    collection = get_contents_collection(client)

    doc_id = str(content_id)

    collection.upsert(
        ids=[doc_id],
        embeddings=[embedding],
        documents=[text],
        metadatas=[
            {
                "content_id": content_id,
                "topic": topic,
                "tags": ", ".join(tags),
            }
        ],
    )

    return doc_id

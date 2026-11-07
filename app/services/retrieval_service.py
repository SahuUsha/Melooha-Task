
from sqlalchemy.orm import Session

from app.models.knowledge_chunk import KnowledgeChunk
from app.services.embedding_service import generate_embeddings


def search_knowledge(
    db: Session,
    question: str,
    top_k: int = 6
) -> list[dict]:

    if not question or not question.strip():
        raise ValueError("Question cannot be empty")

    if top_k < 1 or top_k > 20:
        raise ValueError("top_k must be between 1 and 20")

    # 1. Convert user question into a Qwen embedding
    query_embedding = generate_embeddings(
        [question],
        is_query=True
    )[0]

    # 2. Calculate cosine distance in PostgreSQL
    distance = KnowledgeChunk.embedding.cosine_distance(
        query_embedding
    ).label("distance")

    # 3. Retrieve the most relevant passages
    results = (
        db.query(KnowledgeChunk, distance)
        .order_by(distance)
        .limit(top_k)
        .all()
    )

    # 4. Format retrieved information
    retrieved_chunks = []

    for chunk, score in results:
        similarity = 1 - float(score)

        retrieved_chunks.append({
            "id": chunk.id,
            "content": chunk.content,
            "source": chunk.source,
            "page_number": chunk.page_number,
            "similarity": round(similarity, 4)
        })

    return retrieved_chunks

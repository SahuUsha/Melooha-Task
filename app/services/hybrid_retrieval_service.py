
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.knowledge_chunk import KnowledgeChunk
from app.services.embedding_service import generate_embeddings


def hybrid_search(
    db: Session,
    question: str,
    top_k: int = 5,
    candidate_k: int = 20,
    rrf_k: int = 60,
) -> list[dict]:

    if not question or not question.strip():
        raise ValueError("Question cannot be empty")

    if not 1 <= top_k <= 20:
        raise ValueError("top_k must be between 1 and 20")

    if not 1 <= candidate_k <= 100:
        raise ValueError("candidate_k must be between 1 and 100")

    # 1. Generate the question embedding using existing service
    query_embedding = generate_embeddings(
        [question],
        is_query=True
    )[0]

    # 2. Vector search
    distance = KnowledgeChunk.embedding.cosine_distance(
        query_embedding
    ).label("distance")

    vector_results = (
        db.query(KnowledgeChunk, distance)
        .order_by(distance)
        .limit(candidate_k)
        .all()
    )

    vector_ranks = {
        chunk.id: rank
        for rank, (chunk, _) in enumerate(vector_results, start=1)
    }

    # 3. PostgreSQL full-text keyword search
    keyword_query = text("""
        SELECT
            id,
            ts_rank_cd(
                to_tsvector('english', content),
                plainto_tsquery('english', :question)
            ) AS keyword_score
        FROM knowledge_chunks
        WHERE to_tsvector('english', content)
              @@ plainto_tsquery('english', :question)
        ORDER BY keyword_score DESC
        LIMIT :candidate_k
    """)

    keyword_results = db.execute(
        keyword_query,
        {
            "question": question,
            "candidate_k": candidate_k,
        }
    ).fetchall()

    keyword_ranks = {
        row.id: rank
        for rank, row in enumerate(keyword_results, start=1)
    }

    # 4. Reciprocal Rank Fusion
    all_ids = set(vector_ranks) | set(keyword_ranks)

    rrf_scores = {}

    for chunk_id in all_ids:
        score = 0.0

        if chunk_id in vector_ranks:
            score += 1 / (rrf_k + vector_ranks[chunk_id])

        if chunk_id in keyword_ranks:
            score += 1 / (rrf_k + keyword_ranks[chunk_id])

        rrf_scores[chunk_id] = score

    # 5. Select final top results
    ranked_ids = sorted(
        all_ids,
        key=lambda chunk_id: rrf_scores[chunk_id],
        reverse=True
    )[:top_k]

    # 6. Fetch final chunks
    chunks = (
        db.query(KnowledgeChunk)
        .filter(KnowledgeChunk.id.in_(ranked_ids))
        .all()
    )

    chunks_by_id = {chunk.id: chunk for chunk in chunks}

    final_results = []

    for chunk_id in ranked_ids:
        chunk = chunks_by_id.get(chunk_id)

        if chunk is None:
            continue

        final_results.append({
            "id": chunk.id,
            "content": chunk.content,
            "source": chunk.source,
            "page_number": chunk.page_number,
            "rrf_score": round(rrf_scores[chunk_id], 6),
            "vector_rank": vector_ranks.get(chunk_id),
            "keyword_rank": keyword_ranks.get(chunk_id),
        })

    return final_results

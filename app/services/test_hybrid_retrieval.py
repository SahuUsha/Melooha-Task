
from app.db.database import SessionLocal
from app.services.hybrid_retrieval_service import hybrid_search


def main():
    db = SessionLocal()

    question = "Which zodiac signs are ruled by Jupiter?"

    try:
        results = hybrid_search(
            db=db,
            question=question,
            top_k=5,
            candidate_k=20
        )

        print(f"\nQuestion: {question}")
        print(f"Results found: {len(results)}")

        for rank, result in enumerate(results, start=1):
            print("\n" + "=" * 70)
            print(f"Rank: {rank}")
            print(f"Source: {result['source']}")
            print(f"Page: {result['page_number']}")
            print(f"RRF Score: {result['rrf_score']}")
            print(f"Vector Rank: {result['vector_rank']}")
            print(f"Keyword Rank: {result['keyword_rank']}")
            print(f"Content: {result['content'][:500]}")

    except Exception as error:
        print("Hybrid retrieval failed:", error)

    finally:
        db.close()


if __name__ == "__main__":
    main()

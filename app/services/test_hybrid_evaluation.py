
from app.db.database import SessionLocal
from app.services.hybrid_retrieval_service import hybrid_search
from app.services.evaluation_questions import EVALUATION_QUESTIONS


def main():
    db = SessionLocal()

    try:
        for index, question in enumerate(EVALUATION_QUESTIONS, start=1):
            print("\n" + "=" * 85)
            print(f"QUESTION {index}: {question}")
            print("=" * 85)

            results = hybrid_search(
                db=db,
                question=question,
                top_k=5,
                candidate_k=20
            )

            for rank, result in enumerate(results, start=1):
                print(f"\nRank: {rank}")
                print(f"Source: {result['source']}")
                print(f"Page: {result['page_number']}")
                print(f"RRF Score: {result['rrf_score']}")
                print(f"Vector Rank: {result['vector_rank']}")
                print(f"Keyword Rank: {result['keyword_rank']}")
                print(f"Content: {result['content'][:300]}")

    except Exception as error:
        print("Evaluation failed:", error)

    finally:
        db.close()


if __name__ == "__main__":
    main()

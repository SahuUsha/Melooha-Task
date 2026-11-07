from app.db.database import SessionLocal
from app.services.retrieval_service import search_knowledge


def main():
    db = SessionLocal()

    question = "Which zodiac signs are ruled by Jupiter?"

    try:
        results = search_knowledge(
            db=db,
            question=question,
            top_k=20
        )

        print(f"\nQuestion: {question}")
        print(f"Retrieved candidates: {len(results)}")

        for rank, result in enumerate(results, start=1):
            print("\n" + "-" * 70)
            print(f"Rank: {rank}")
            print(f"Source: {result['source']}")
            print(f"Page: {result['page_number']}")
            print(f"Similarity: {result['similarity']}")
            print(f"Content: {result['content'][:500]}")

    except Exception as error:
        print("Retrieval failed:", error)

    finally:
        db.close()


if __name__ == "__main__":
    main()
from app.db.database import SessionLocal
from app.services.retrieval_service import search_knowledge
from app.services.evaluation_questions import EVALUATION_QUESTIONS


def main():
    db = SessionLocal()

    try:
        for index, question in enumerate(EVALUATION_QUESTIONS, start=1):

            print("\n" + "=" * 80)
            print(f"QUESTION {index}: {question}")
            print("=" * 80)

            results = search_knowledge(
                db=db,
                question=question,
                top_k=5
            )

            if not results:
                print("No results found.")
                continue

            for rank, result in enumerate(results, start=1):
                print(f"\nRank: {rank}")
                print(f"Source: {result['source']}")
                print(f"Page: {result['page_number']}")
                print(f"Similarity: {result['similarity']}")
                print(f"Content: {result['content'][:350]}")

    except Exception as error:
        print("\nEvaluation failed:", error)

    finally:
        db.close()


if __name__ == "__main__":
    main()

from app.db.database import SessionLocal
from app.services.retrieval_service import search_knowledge


def main():

    db = SessionLocal()

    try:
        question = question = "Which zodiac signs are ruled by Venus?"

        print("\nUser question:", question)
        print("\nSearching astrology knowledge...\n")

        results = search_knowledge(
            db=db,
            question=question,
            top_k=5
        )

        if not results:
            print("No knowledge chunks found.")
            return

        for index, result in enumerate(results, start=1):

            print(f"\nResult {index}")
            print("-" * 50)

            print("Source:", result["source"])
            print("Page:", result["page_number"])
            print("Similarity:", result["similarity"])
            print("Content:", result["content"][:500])

    except Exception as error:
        print("Retrieval failed:", error)

    finally:
        db.close()


if __name__ == "__main__":
    main()

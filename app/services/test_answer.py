
from app.db.database import SessionLocal
from app.services.answer_service import answer_question


def main():
    db = SessionLocal()

    try:
        question ="What is the current stock price of Apple?"

        print("\nQuestion:", question)
        print("\nGenerating grounded answer...\n")

        result = answer_question(
            db=db,
            question=question,
            top_k=5,
        )

        print("=" * 60)
        print("ANSWER")
        print("=" * 60)
        print(result["answer"])

        print("\nCITATIONS")
        print("=" * 60)

        for citation in result["citations"]:
            print(
                f"Source: {citation['source']} | "
                f"Page: {citation['page_number']}"
            )

        print("\nProvider:", result["provider"])
        print("Retrieved passages:", result["retrieved_count"])

    except Exception as error:
        print("\nTest failed:", str(error))

    finally:
        db.close()


if __name__ == "__main__":
    main()

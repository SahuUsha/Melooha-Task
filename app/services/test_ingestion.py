from pathlib import Path

from app.db.database import SessionLocal
from app.services.pdf_service import ingest_pdf


PROJECT_ROOT = Path(__file__).resolve().parents[3]

PDF_FILES = [
    PROJECT_ROOT / "books" / "uploads" / "vedic_astrology.pdf",
    PROJECT_ROOT / "books" / "uploads" / "zodiac_notes.pdf",
]


def main():
    db = SessionLocal()

    try:
        for pdf_path in PDF_FILES:

            print(f"\nProcessing: {pdf_path.name}")

            if not pdf_path.exists():
                print(f"PDF not found: {pdf_path}")
                continue

            with open(pdf_path, "rb") as file:
                pdf_bytes = file.read()

            result = ingest_pdf(
                db=db,
                pdf_bytes=pdf_bytes,
                filename=pdf_path.name
            )

            print("Ingestion successful!")
            print(result)

    except Exception as error:
        print("Ingestion failed:", error)

    finally:
        db.close()


if __name__ == "__main__":
    main()
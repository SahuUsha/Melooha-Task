from pathlib import Path

from app.services.pdf_service import (
    extract_pdf_pages,
    create_chunks
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]

PDF_PATH = PROJECT_ROOT / "books" / "uploads" / "birth_chart.pdf"

def main():
    if not PDF_PATH.exists():
        print("PDF not found:", PDF_PATH.resolve())
        return

    pdf_bytes = PDF_PATH.read_bytes()

    pages = extract_pdf_pages(pdf_bytes)

    print("Total pages with text:", len(pages))

    if not pages:
        print("No text extracted. This PDF may be scanned.")
        return

    for page in pages[:2]:
        chunks = create_chunks(page["text"])

        print("\nPage:", page["page_number"])
        print("Extracted text:", page["text"][:300])
        print("Chunks:", len(chunks))


if __name__ == "__main__":
    main()
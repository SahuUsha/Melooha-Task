
import re
import pymupdf

from sqlalchemy.orm import Session

from app.models.knowledge_chunk import KnowledgeChunk
from app.services.embedding_service import generate_embeddings_in_batches


# 1. Extract PDF text page by page
def extract_pdf_pages(pdf_bytes: bytes) -> list[dict]:
    document = pymupdf.open(
        stream=pdf_bytes,
        filetype="pdf"
    )

    pages = []

    try:
        for page_number, page in enumerate(document, start=1):
            text = page.get_text("text")

            text = re.sub(r"[ \t]+", " ", text)
            text = re.sub(r"\n{3,}", "\n\n", text)
            text = text.strip()

            if text:
                pages.append({
                    "page_number": page_number,
                    "text": text
                })

    finally:
        document.close()

    return pages


# 2. Split text into overlapping chunks
def create_chunks(
    text: str,
    chunk_size: int = 1200,
    overlap: int = 200
) -> list[str]:

    if overlap >= chunk_size:
        raise ValueError("Overlap must be smaller than chunk size")

    chunks = []
    start = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end == len(text):
            break

        start = end - overlap

    return chunks


# 3. Extract, embed and store PDF knowledge
def ingest_pdf(
    db: Session,
    pdf_bytes: bytes,
    filename: str
) -> dict:

    pages = extract_pdf_pages(pdf_bytes)

    if not pages:
        raise ValueError("No readable text found in this PDF")

    chunk_records = []

    # Generate chunks page by page
    for page in pages:
        chunks = create_chunks(page["text"])

        for chunk in chunks:
            chunk_records.append({
                "content": chunk,
                "source": filename,
                "page_number": page["page_number"]
            })

    if not chunk_records:
        raise ValueError("No chunks generated")

    print(f"Pages extracted: {len(pages)}")
    print(f"Total chunks: {len(chunk_records)}")

    # 4. Generate Qwen embeddings through Hugging Face
    texts = [
        record["content"]
        for record in chunk_records
    ]

    embeddings = generate_embeddings_in_batches(
        texts,
        batch_size=16,
        is_query=False
    )

    if len(embeddings) != len(chunk_records):
        raise ValueError("Embedding count does not match chunk count")

    # 5. Prepare database records
    db_records = []

    for record, embedding in zip(chunk_records, embeddings):
        db_records.append(
            KnowledgeChunk(
                content=record["content"],
                source=record["source"],
                page_number=record["page_number"],
                embedding=embedding
            )
        )

    # 6. Save records in Neon PostgreSQL
    try:
        # Replace existing ingestion of the same filename
        db.query(KnowledgeChunk).filter(
            KnowledgeChunk.source == filename
        ).delete(synchronize_session=False)

        db.add_all(db_records)

        # Commit changes to Neon
        db.commit()

        print(f"Successfully stored {len(db_records)} chunks in Neon!")

    except Exception:
        db.rollback()
        raise

    return {
        "filename": filename,
        "pages_processed": len(pages),
        "chunks_stored": len(db_records),
        "embedding_model": "Qwen/Qwen3-Embedding-0.6B",
        "embedding_dimension": 1024
    }

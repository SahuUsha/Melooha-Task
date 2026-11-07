
from app.services.embedding_service import (
    generate_embeddings,
    generate_embeddings_in_batches,
)


def main():
    documents = [
        "The Sun represents the soul in Vedic astrology.",
        "The Moon represents the mind and emotions.",
        "Jupiter is associated with wisdom and knowledge.",
    ]

    print("Testing document embeddings...")

    document_vectors = generate_embeddings_in_batches(
        documents,
        batch_size=2,
        is_query=False,
    )

    print("Document vectors:", len(document_vectors))
    print("Document dimensions:", len(document_vectors[0]))

    question = "What does Jupiter represent in Vedic astrology?"

    print("\nTesting query embedding...")

    query_vectors = generate_embeddings(
        [question],
        is_query=True,
    )

    print("Query vectors:", len(query_vectors))
    print("Query dimensions:", len(query_vectors[0]))

    print("\nHugging Face embedding test successful!")


if __name__ == "__main__":
    main()

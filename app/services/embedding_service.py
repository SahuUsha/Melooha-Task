
import time
import numpy as np
from huggingface_hub import InferenceClient

from app.core.config import settings


EMBEDDING_MODEL = "Qwen/Qwen3-Embedding-0.6B"
EMBEDDING_DIMENSION = 1024

# One hosted API client; no model is downloaded locally.
client = InferenceClient(
    provider="deepinfra",
    token=settings.HF_TOKEN,
    timeout=90,
)

QUERY_INSTRUCTION = (
    "Given a user's Vedic astrology question, "
    "retrieve relevant passages from Vedic astrology books."
)


def generate_embeddings(
    texts: list[str],
    is_query: bool = False
) -> list[list[float]]:

    if not texts:
        return []

    # Qwen recommends an instruction for retrieval queries.
    # Documents/passages are embedded without this instruction.
    if is_query:
        inputs = [
            f"Instruct: {QUERY_INSTRUCTION}\nQuery: {text}"
            for text in texts
        ]
    else:
        inputs = texts

    for attempt in range(3):
        try:
            response = client.feature_extraction(
                text=inputs,
                model=EMBEDDING_MODEL,
            )

            vectors = np.asarray(response, dtype=np.float32)

            if vectors.ndim == 1:
                vectors = vectors.reshape(1, -1)

            if vectors.shape[0] != len(texts):
                raise ValueError(
                    f"Expected {len(texts)} embeddings, "
                    f"received {vectors.shape[0]}"
                )

            if vectors.shape[1] != EMBEDDING_DIMENSION:
                raise ValueError(
                    f"Expected {EMBEDDING_DIMENSION} dimensions, "
                    f"received {vectors.shape[1]}"
                )

            if not np.isfinite(vectors).all():
                raise ValueError("Embedding response contains invalid values")

            return vectors.tolist()

        except Exception as error:
            if attempt == 2:
                raise RuntimeError(
                    f"Hugging Face embedding API failed: {error}"
                ) from error

            wait_seconds = 2 ** (attempt + 1)
            print(
                f"Embedding API attempt {attempt + 1} failed: {error}. "
                f"Retrying in {wait_seconds} seconds."
            )
            time.sleep(wait_seconds)


def generate_embeddings_in_batches(
    texts: list[str],
    batch_size: int = 16,
    is_query: bool = False,
) -> list[list[float]]:

    if not texts:
        return []

    all_embeddings = []

    for start in range(0, len(texts), batch_size):
        batch = texts[start:start + batch_size]

        batch_number = start // batch_size + 1

        print(
            f"Embedding batch {batch_number}: "
            f"{len(batch)} texts"
        )

        embeddings = generate_embeddings(
            batch,
            is_query=is_query,
        )

        all_embeddings.extend(embeddings)

    if len(all_embeddings) != len(texts):
        raise ValueError(
            f"Embedding count mismatch: "
            f"{len(texts)} texts, {len(all_embeddings)} vectors"
        )

    return all_embeddings

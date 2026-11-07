
import re

from sqlalchemy.orm import Session
from google import genai
from groq import Groq

from app.core.config import settings
from app.services.retrieval_service import search_knowledge
from app.services.chart_retrieval_service import get_user_chart_facts


GEMINI_MODEL = "gemini-2.5-flash"
GROQ_MODEL = "llama-3.3-70b-versatile"

SIMILARITY_THRESHOLD = 0.40

INSUFFICIENT_ANSWER = (
    "I don't have enough information in my available astrology "
    "knowledge to answer this question reliably."
)


def build_prompt(
    question: str,
    chunks: list[dict],
    chart_facts: list[dict] | None = None,
) -> str:
    """Build a prompt using PDF evidence and personal chart facts."""

    evidence_sections = []

    for index, chunk in enumerate(chunks, start=1):
        evidence_sections.append(
            f"""
[E{index}]
Source: {chunk['source']}
Page: {chunk['page_number']}
Content:
{chunk['content']}
"""
        )

    evidence = "\n".join(evidence_sections)

    chart_sections = []

    for fact in chart_facts or []:
        chart_sections.append(
            f"""
Chart fact: {fact['fact_key']}
Value: {fact['fact_value']}
Source: {fact['source']}
"""
        )

    chart_evidence = "\n".join(chart_sections)

    return f"""
You are Melooha, a knowledge-base-grounded Vedic astrology assistant.

IMPORTANT RULES:

1. Use ONLY the supplied PDF evidence and personal chart facts.
2. Never use pretrained or general astrology knowledge.
3. Never invent planetary positions, signs, houses, degrees or retrograde status.
4. Use personal chart facts only for questions about the user's own birth chart.
5. Use PDF evidence for general astrology knowledge and interpretations.
6. Clearly distinguish calculated chart facts from general interpretations.
7. Every factual paragraph must contain supporting citations.
8. Cite PDF evidence using [E1], [E2], etc.
9. Cite personal chart facts using their exact fact keys, for example:
   [Chart: jupiter.sign]
10. Never invent a chart fact key or a PDF evidence ID.
11. If the available evidence is insufficient, respond exactly with:
    INSUFFICIENT_EVIDENCE
12. Do not make assumptions or fill missing information using general knowledge.
13. Prefer short, direct answers.

USER QUESTION:
{question}

PERSONAL BIRTH CHART FACTS:
{chart_evidence if chart_evidence else "No personal chart facts available."}

ASTROLOGY KNOWLEDGE BASE:
{evidence if evidence else "No relevant PDF evidence available."}

Answer using only the supplied evidence.
"""



def generate_with_gemini(prompt: str, on_token=None) -> str:
    """Generate an answer using Gemini, optionally streaming tokens."""

    client = genai.Client(api_key=settings.GEMINI_API_KEY)

    if on_token is None:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
        )

        if not response.text:
            raise RuntimeError("Gemini returned an empty response.")

        return response.text.strip()

    answer_parts = []

    response_stream = client.models.generate_content_stream(
        model=GEMINI_MODEL,
        contents=prompt,
    )

    for chunk in response_stream:
        if chunk.text:
            answer_parts.append(chunk.text)
            on_token(chunk.text)

    answer = "".join(answer_parts).strip()

    if not answer:
        raise RuntimeError("Gemini returned an empty response.")

    return answer




def generate_with_groq(prompt: str, on_token=None) -> str:
    """Generate an answer using Groq, optionally streaming tokens."""

    if not settings.GROQ_API_KEY:
        raise RuntimeError("Groq API key is not configured.")

    client = Groq(api_key=settings.GROQ_API_KEY)

    if on_token is None:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an evidence-grounded Vedic astrology "
                        "assistant. Follow the supplied instructions "
                        "strictly and never invent facts or citations."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )

        answer = response.choices[0].message.content

        if not answer:
            raise RuntimeError("Groq returned an empty response.")

        return answer.strip()

    response_stream = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an evidence-grounded Vedic astrology "
                    "assistant. Follow the supplied instructions "
                    "strictly and never invent facts or citations."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        stream=True,
    )

    answer_parts = []

    for chunk in response_stream:
        content = chunk.choices[0].delta.content

        if content:
            answer_parts.append(content)
            on_token(content)

    answer = "".join(answer_parts).strip()

    if not answer:
        raise RuntimeError("Groq returned an empty response.")

    return answer



def answer_question(
     db: Session,
    question: str,
    user_id: int,
    top_k: int = 5,
    on_token=None,
) -> dict:
    """
    Retrieve PDF knowledge and personal chart facts,
    then generate a grounded answer.

    Gemini is primary. Groq is the fallback.
    """

    if not question or not question.strip():
        raise ValueError("Question cannot be empty.")

    # 1. Retrieve personal chart facts for this user.
    chart_facts = get_user_chart_facts(
        db=db,
        user_id=user_id,
    )

    # 2. Retrieve relevant PDF passages.
    # No embedding request is made for chart fact retrieval.
    chunks = search_knowledge(
        db=db,
        question=question.strip(),
        top_k=top_k,
    )

    chunks = [
        chunk
        for chunk in chunks
        if chunk["similarity"] >= SIMILARITY_THRESHOLD
    ]

    # 3. If neither source contains evidence, do not call an LLM.
    if not chunks and not chart_facts:
        return {
            "answer": INSUFFICIENT_ANSWER,
            "citations": [],
            "chart_citations": [],
            "provider": None,
            "retrieved_count": 0,
        }

    # 4. Prepare the prompt.
    prompt = build_prompt(
        question=question.strip(),
        chunks=chunks,
        chart_facts=chart_facts,
    )

    # 5. Gemini primary, Groq fallback.
    try:
        raw_answer = generate_with_gemini(
        prompt,
        on_token=on_token,
        )
        provider = "gemini"

    except Exception as gemini_error:
        print(f"Gemini failed: {gemini_error}")
        print("Trying Groq fallback...")

        if on_token is not None:
             on_token(None)

        try:
            raw_answer = generate_with_groq(
             prompt,
             on_token=on_token,
        )
            provider = "groq"

        except Exception as groq_error:
            print(f"Groq failed: {groq_error}")
            raise RuntimeError(
                "Both Gemini and Groq failed to generate an answer."
            ) from groq_error

    # 6. Handle insufficient evidence.
    if "INSUFFICIENT_EVIDENCE" in raw_answer:
        return {
            "answer": INSUFFICIENT_ANSWER,
            "citations": [],
            "chart_citations": [],
            "provider": provider,
            "retrieved_count": len(chunks),
        }

    # 7. Validate PDF evidence IDs.
    citation_groups = re.findall(
        r"\[(E\d+(?:\s*,\s*E\d+)*)\]",
        raw_answer,
    )

    used_ids = []

    for group in citation_groups:
        used_ids.extend(re.findall(r"E(\d+)", group))

    valid_ids = {
        str(index)
        for index in range(1, len(chunks) + 1)
    }

    if any(
        evidence_id not in valid_ids
        for evidence_id in used_ids
    ):
        return {
            "answer": INSUFFICIENT_ANSWER,
            "citations": [],
            "chart_citations": [],
            "provider": provider,
            "retrieved_count": len(chunks),
        }

    # 8. Validate personal chart fact references.
    valid_chart_keys = {
        fact["fact_key"]
        for fact in chart_facts
    }

    chart_reference_pattern = (
    r"\[(?!E\d+\])(?:Chart:\s*)?([a-zA-Z][a-zA-Z0-9_.]*)\]"
)

    used_chart_keys = re.findall(
        chart_reference_pattern,
        raw_answer,
    )

    if any(
        key not in valid_chart_keys
        for key in used_chart_keys
    ):
        return {
            "answer": INSUFFICIENT_ANSWER,
            "citations": [],
            "chart_citations": [],
            "provider": provider,
            "retrieved_count": len(chunks),
        }

    # 9. Every factual answer must cite at least one valid source.
    if not used_ids and not used_chart_keys:
        return {
            "answer": INSUFFICIENT_ANSWER,
            "citations": [],
            "chart_citations": [],
            "provider": provider,
            "retrieved_count": len(chunks),
        }

    # 10. Replace PDF evidence IDs with actual PDF citations.
    citations = []
    cited_ids = set()

    def replace_citation_group(match):
        evidence_numbers = re.findall(r"E(\d+)", match.group(0))
        replacements = []

        for evidence_id in evidence_numbers:
            if evidence_id in cited_ids:
                continue

            cited_ids.add(evidence_id)
            chunk = chunks[int(evidence_id) - 1]

            citations.append({
                "source": chunk["source"],
                "page_number": chunk["page_number"],
            })

            if chunk["page_number"] is not None:
                replacements.append(
                    f"[{chunk['source']}, p. {chunk['page_number']}]"
                )
            else:
                replacements.append(f"[{chunk['source']}]")

        return " ".join(replacements)

    final_answer = re.sub(
        r"\[(?:E\d+)(?:\s*,\s*E\d+)*\]",
        replace_citation_group,
        raw_answer,
    )

    # 11. Replace chart references with verified chart fact citations.
    chart_citations = []
    cited_chart_keys = set()

    chart_fact_lookup = {
        fact["fact_key"]: fact
        for fact in chart_facts
    }

    def replace_chart_reference(match):
        fact_key = match.group(1)

        if fact_key in cited_chart_keys:
            return f"[Chart: {fact_key}]"

        cited_chart_keys.add(fact_key)

        fact = chart_fact_lookup[fact_key]

        chart_citations.append({
            "fact_key": fact["fact_key"],
            "fact_value": fact["fact_value"],
            "source": fact["source"],
        })

        return f"[Chart: {fact_key}]"

    final_answer = re.sub(
        chart_reference_pattern,
        replace_chart_reference,
        final_answer,
    ).strip()


# 12. Reject any remaining fabricated evidence references.
    if re.search(r"\[E\d+\]", final_answer):
       return {
        "answer": INSUFFICIENT_ANSWER,
        "citations": [],
        "chart_citations": [],
        "provider": provider,
        "retrieved_count": len(chunks),
      }

    return {
    "answer": final_answer,
    "citations": citations,
    "chart_citations": chart_citations,
    "provider": provider,
    "retrieved_count": len(chunks),
}

import json
import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import KnowledgeChunkModel, KnowledgeDocumentModel
from app.schemas import Citation, DocumentStatus
from app.services.embeddings import EmbeddingError, EmbeddingProvider, cosine_similarity, get_embedding_provider


def _terms(text: str) -> set[str]:
    normalized = text.lower()
    latin_words = re.findall(r"[a-z0-9]{2,}", normalized)
    chinese = "".join(re.findall(r"[\u4e00-\u9fff]", normalized))
    chinese_bigrams = [chinese[index:index + 2] for index in range(len(chinese) - 1)]
    return set(latin_words + chinese_bigrams)


def _chunk_embedding(chunk: KnowledgeChunkModel) -> list[float] | None:
    if not chunk.embedding:
        return None
    try:
        vector = json.loads(chunk.embedding)
    except json.JSONDecodeError:
        return None
    if not isinstance(vector, list) or not vector or not all(isinstance(value, (int, float)) for value in vector):
        return None
    return [float(value) for value in vector]


def search_published_knowledge(
    session: Session,
    query: str,
    limit: int = 3,
    embedding_provider: EmbeddingProvider | None = None,
) -> list[Citation]:
    query_terms = _terms(query)
    provider = embedding_provider or get_embedding_provider()
    try:
        query_embedding = provider.embed([query])[0] if provider else None
    except EmbeddingError:
        query_embedding = None
    rows = session.execute(
        select(KnowledgeChunkModel, KnowledgeDocumentModel)
        .join(KnowledgeDocumentModel, KnowledgeChunkModel.document_id == KnowledgeDocumentModel.id)
        .where(KnowledgeDocumentModel.status == DocumentStatus.published.value)
    ).all()
    ranked: list[tuple[float, Citation]] = []
    for chunk, document in rows:
        overlap = query_terms.intersection(_terms(chunk.content))
        lexical_score = len(overlap) / len(query_terms) if query_terms else 0.0
        vector_score = cosine_similarity(query_embedding, _chunk_embedding(chunk) or []) if query_embedding else 0.0
        if lexical_score == 0 and vector_score <= 0:
            continue
        # Vector candidates are re-ranked with matching course terms so citations remain inspectable.
        score = (vector_score * 0.75 + lexical_score * 0.25) if query_embedding else lexical_score
        ranked.append(
            (
                score,
                Citation(
                    document_id=document.id,
                    title=document.title,
                    course_name=document.course_name,
                    source_locator=chunk.source_locator,
                    excerpt=chunk.content[:280],
                    score=round(score, 3),
                ),
            )
        )
    ranked.sort(key=lambda item: item[0], reverse=True)
    return [citation for _, citation in ranked[:limit]]

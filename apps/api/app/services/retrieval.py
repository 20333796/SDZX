import json
import re
from urllib.parse import quote

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ExternalResourceModel, KnowledgeChunkModel, KnowledgeDocumentModel
from app.schemas import ChatResourceReference, Citation, DocumentStatus
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


_MENTOR_REFERENCES = (
    ChatResourceReference(
        id="mentor-graph",
        title="导师图谱",
        category="mentor",
        provider="中国石油大学（北京）教师平台",
        description="按学院、职称和研究方向浏览全校公开教师信息。",
        route="/teaching/mentor-graph",
        embedded_url="/teaching/mentor-graph",
    ),
    ChatResourceReference(
        id="geophysics-mentors",
        title="地球物理学院导师",
        category="mentor",
        provider="中国石油大学（北京）教师平台",
        description="查看地球物理学院教师、研究方向与官网个人页。",
        route="/teaching/mentor-graph?school=地球物理学院",
        embedded_url="/teaching/mentor-graph?school=地球物理学院",
    ),
    ChatResourceReference(
        id="geoscience-mentors",
        title="地球科学学院导师",
        category="mentor",
        provider="中国石油大学（北京）教师平台",
        description="查看地球科学学院教师、研究方向与官网个人页。",
        route="/teaching/mentor-graph?school=地球科学学院",
        embedded_url="/teaching/mentor-graph?school=地球科学学院",
    ),
)

_BUILTIN_RESOURCES = (
    ("petroleum-geology-ai-foundation", "油矿地质学 AI 课程", "courses", "油矿地质学、石油地质学"),
    ("reservoir-characterization", "储层表征与建模", "courses", "储层表征、储层建模"),
    ("oil-gas-exploration-graduate", "Oil and Gas Field Exploration 研究生资源", "courses", "油气田勘探、勘探"),
    ("seismic-exploration-vr", "油气地震勘探虚拟仿真实验", "practice", "地震勘探、地震实验、仿真"),
    ("clastic-rock-vr", "碎屑岩镜下观察虚拟仿真", "practice", "碎屑岩、显微观察、虚拟仿真"),
)


def _query_subject(query: str, category: str) -> str | None:
    """Extract the human subject after common Chinese request phrases."""
    text = re.sub(r"[？?！!。，,；;：:]", " ", query).strip()
    if category == "mentor":
        match = re.search(r"(?:了解|介绍|查询|查找|查一下|认识|联系)\s*(?:一下)?\s*([\u4e00-\u9fff]{2,5})\s*(?:老师|导师|教授|副教授|讲师)", text)
        if match:
            return match.group(1)
        match = re.search(r"([\u4e00-\u9fff]{2,5})\s*(?:老师|导师|教授|副教授|讲师)", text)
        return match.group(1) if match else None
    match = re.search(r"(?:了解|介绍|查询|查找|学习)\s*([^ ]{2,30}?)\s*(?:课程|课)", text)
    if match:
        return match.group(1).strip()
    return None


def search_portal_resources(session: Session, query: str, limit: int = 8) -> list[ChatResourceReference]:
    """Find first-party portal resources that can be opened from an answer."""
    terms = _terms(query)
    resource_rows = session.scalars(
        select(ExternalResourceModel)
        .where(ExternalResourceModel.status == "active")
        .order_by(ExternalResourceModel.sort_order, ExternalResourceModel.title)
    ).all()
    ranked: list[tuple[float, ChatResourceReference]] = []
    category_route = {"courses": "/source/courses", "practice": "/practice/simulation"}
    candidate_rows = list(resource_rows)
    known_ids = {resource.id for resource in candidate_rows}
    for resource_id, title, category, aliases in _BUILTIN_RESOURCES:
        if resource_id not in known_ids:
            candidate_rows.append(type("BuiltinResource", (), {
                "id": resource_id, "title": title, "provider": "中国石油大学（北京）教学资源",
                "description": f"门户已收录的{title}入口。", "category": category, "url": None,
            })())
    for resource in candidate_rows:
        if resource.category not in category_route:
            continue
        searchable = " ".join((resource.title, resource.provider, resource.description, resource.category))
        overlap = terms.intersection(_terms(searchable))
        keyword_bonus = 0.25 if resource.category == "courses" and any(word in query for word in ("课程", "课", "学习")) else 0
        keyword_bonus += 0.25 if resource.category == "practice" and any(word in query for word in ("仿真", "实验", "实训")) else 0
        score = len(overlap) + keyword_bonus
        if score <= 0:
            continue
        url = str(resource.url) if resource.url else None
        subject = _query_subject(query, resource.category)
        base_route = category_route.get(resource.category)
        route = f"{base_route}?q={quote(subject)}" if subject and base_route else base_route
        ranked.append((score, ChatResourceReference(
            id=resource.id,
            title=resource.title,
            category=resource.category,
            provider=resource.provider,
            description=resource.description,
            url=url,
            embedded_url=url,
            route=route,
        )))

    mentor_terms = ("导师", "老师", "教师", "学院", "研究方向", "教授", "副教授", "讲师", "地球物理", "地球科学")
    if any(term in query for term in mentor_terms):
        subject = _query_subject(query, "mentor")
        mentor_score = 2.0 + sum(1 for term in mentor_terms if term in query) * 0.1
        references = _MENTOR_REFERENCES[:1] if subject else _MENTOR_REFERENCES
        for index, reference in enumerate(references):
            if subject:
                reference = reference.model_copy(update={
                    "title": f"{subject} · 导师信息",
                    "description": f"在全校官方教师图谱中定位“{subject}”，查看所属单位、职称和研究方向。",
                    "route": f"/teaching/mentor-graph?mentor={quote(subject)}",
                    "embedded_url": f"/teaching/mentor-graph?mentor={quote(subject)}",
                })
            ranked.append((mentor_score - index * 0.01 + (1 if subject else 0), reference))
    ranked.sort(key=lambda item: item[0], reverse=True)
    seen: set[str] = set()
    results: list[ChatResourceReference] = []
    for _, resource in ranked:
        if resource.id in seen:
            continue
        seen.add(resource.id)
        results.append(resource)
        if len(results) >= limit:
            break
    return results

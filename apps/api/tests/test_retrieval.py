from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database import Base
from app.models import KnowledgeChunkModel, KnowledgeDocumentModel
from app.services.retrieval import search_published_knowledge


class StubEmbeddingProvider:
    model_name = "test-embedding"

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [[0.0, 1.0] for _ in texts]


def test_search_returns_only_published_knowledge_with_source() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        published = KnowledgeDocumentModel(
            id="published-document",
            title="油矿地质学讲义",
            document_type="courseware",
            original_filename="petroleum.md",
            content_type="text/markdown",
            object_key="documents/petroleum.md",
            checksum="a" * 64,
            byte_size=10,
            status="published",
            version=1,
            created_by="teacher-001",
        )
        hidden = KnowledgeDocumentModel(
            id="hidden-document",
            title="未审核资料",
            document_type="courseware",
            original_filename="hidden.md",
            content_type="text/markdown",
            object_key="documents/hidden.md",
            checksum="b" * 64,
            byte_size=10,
            status="parsed",
            version=1,
            created_by="teacher-001",
        )
        session.add_all([published, hidden])
        session.add_all(
            [
                KnowledgeChunkModel(
                    id="published-chunk",
                    document_id=published.id,
                    ordinal=0,
                    content="储层识别需要综合 GR、RT 与孔隙度曲线。",
                    content_hash="c" * 64,
                    source_locator="chunk:1",
                ),
                KnowledgeChunkModel(
                    id="hidden-chunk",
                    document_id=hidden.id,
                    ordinal=0,
                    content="储层识别的未审核结论。",
                    content_hash="d" * 64,
                    source_locator="chunk:1",
                ),
            ]
        )
        session.commit()

        citations = search_published_knowledge(session, "如何识别储层 GR 曲线")
        assert [citation.document_id for citation in citations] == [published.id]
        assert citations[0].source_locator == "chunk:1"


def test_search_can_rank_published_chunks_by_vector_similarity() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        document = KnowledgeDocumentModel(
            id="vector-document",
            title="储层表征讲义",
            document_type="courseware",
            original_filename="reservoir.md",
            content_type="text/markdown",
            object_key="documents/reservoir.md",
            checksum="e" * 64,
            byte_size=10,
            status="published",
            version=1,
            created_by="teacher-001",
        )
        session.add(document)
        session.add_all(
            [
                KnowledgeChunkModel(
                    id="vector-low",
                    document_id=document.id,
                    ordinal=0,
                    content="无关的教学说明。",
                    content_hash="f" * 64,
                    source_locator="chunk:1",
                    embedding="[1.0,0.0]",
                    embedding_model="test-embedding",
                ),
                KnowledgeChunkModel(
                    id="vector-high",
                    document_id=document.id,
                    ordinal=1,
                    content="储层表征包含孔隙度证据。",
                    content_hash="g" * 64,
                    source_locator="chunk:2",
                    embedding="[0.0,1.0]",
                    embedding_model="test-embedding",
                ),
            ]
        )
        session.commit()

        citations = search_published_knowledge(session, "未出现的语义查询", embedding_provider=StubEmbeddingProvider())
        assert [citation.source_locator for citation in citations] == ["chunk:2"]
        assert citations[0].score == 0.75

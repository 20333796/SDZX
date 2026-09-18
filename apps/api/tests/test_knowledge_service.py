from io import BytesIO

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database import Base
from app.models import KnowledgeChunkModel, KnowledgeDocumentModel
from app.schemas import DocumentStatus
from app.services.ingestion import index_reviewed_documents, parse_document
from app.services.knowledge import create_document, get_document, transition_document
from app.storage import LocalObjectStore


class StubEmbeddingProvider:
    model_name = "test-embedding"

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [[float(index + 1), 0.5] for index, _ in enumerate(texts)]


def test_document_upload_and_review_state_machine(tmp_path) -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    store = LocalObjectStore(str(tmp_path / "objects"))

    with Session(engine) as session:
        document = create_document(
            session=session,
            store=store,
            stream=BytesIO(b"Reservoir characterization teaching note"),
            filename="reservoir-note.txt",
            content_type="text/plain",
            title="储层表征教学讲义",
            document_type="courseware",
            course_name="油矿地质学",
            created_by="teacher-001",
            max_bytes=1024,
        )
        assert document.status == DocumentStatus.uploaded
        assert (tmp_path / "objects" / "documents" / f"{document.id}.txt").exists()

        model = get_document(session, document.id)
        assert model is not None
        for target in (DocumentStatus.parsed, DocumentStatus.reviewed, DocumentStatus.indexed, DocumentStatus.published):
            document = transition_document(session, model, target, "teacher-001")
            model = get_document(session, document.id)
            assert model is not None
        assert document.status == DocumentStatus.published
        assert document.reviewed_by == "teacher-001"


def test_document_rejects_unknown_file_format(tmp_path) -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        try:
            create_document(
                session=session,
                store=LocalObjectStore(str(tmp_path / "objects")),
                stream=BytesIO(b"data"),
                filename="well-log.las",
                content_type="text/plain",
                title="不支持的示例",
                document_type="courseware",
                course_name=None,
                created_by="teacher-001",
                max_bytes=1024,
            )
        except ValueError as error:
            assert "Unsupported" in str(error)
        else:
            raise AssertionError("LAS files must use the well-log upload flow")


def test_worker_parses_uploaded_text_into_knowledge_chunks(tmp_path) -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    store = LocalObjectStore(str(tmp_path / "objects"))
    with Session(engine) as session:
        document = create_document(
            session=session,
            store=store,
            stream=BytesIO("储层具有孔隙度和渗透率。\n\nGR 曲线可辅助判断泥质含量。".encode()),
            filename="logging-note.md",
            content_type="text/markdown",
            title="测井课程讲义",
            document_type="courseware",
            course_name="地球物理测井",
            created_by="teacher-001",
            max_bytes=1024,
        )
        model = get_document(session, document.id)
        assert model is not None
        assert parse_document(session, store, model) == 1
        assert model.status == DocumentStatus.parsed.value
        chunks = session.query(KnowledgeChunkModel).filter_by(document_id=document.id).all()
        assert chunks[0].content.startswith("储层具有孔隙度")


def test_worker_indexes_reviewed_document_chunks(tmp_path) -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    store = LocalObjectStore(str(tmp_path / "objects"))
    with Session(engine) as session:
        document = create_document(
            session=session,
            store=store,
            stream=BytesIO("储层具有孔隙度和渗透率。".encode()),
            filename="reservoir-note.md",
            content_type="text/markdown",
            title="储层课程讲义",
            document_type="courseware",
            course_name="油矿地质学",
            created_by="teacher-001",
            max_bytes=1024,
        )
        model = get_document(session, document.id)
        assert model is not None
        parse_document(session, store, model)
        transition_document(session, model, DocumentStatus.reviewed, "teacher-001")

        assert index_reviewed_documents(session, StubEmbeddingProvider()) == 1
        indexed = get_document(session, document.id)
        assert indexed is not None
        assert indexed.status == DocumentStatus.indexed.value
        chunk = session.query(KnowledgeChunkModel).filter_by(document_id=document.id).one()
        assert chunk.embedding == "[1.0,0.5]"
        assert chunk.embedding_model == "test-embedding"

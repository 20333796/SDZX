import hashlib
from datetime import UTC, datetime
from pathlib import Path
from typing import BinaryIO
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import KnowledgeDocumentModel
from app.schemas import DocumentStatus, KnowledgeDocument
from app.storage import ObjectStore

ALLOWED_SUFFIXES = {".pdf", ".docx", ".pptx", ".txt", ".md"}
TRANSITIONS: dict[DocumentStatus, set[DocumentStatus]] = {
    DocumentStatus.uploaded: {DocumentStatus.parsed, DocumentStatus.rejected},
    DocumentStatus.parsed: {DocumentStatus.reviewed, DocumentStatus.rejected},
    DocumentStatus.reviewed: {DocumentStatus.indexed, DocumentStatus.rejected},
    DocumentStatus.indexed: {DocumentStatus.published, DocumentStatus.rejected},
    DocumentStatus.published: set(),
    DocumentStatus.rejected: set(),
}


def _hash_stream(stream: BinaryIO, max_bytes: int) -> tuple[str, int]:
    stream.seek(0)
    digest = hashlib.sha256()
    size = 0
    while chunk := stream.read(1_048_576):
        size += len(chunk)
        if size > max_bytes:
            raise ValueError("Document exceeds the upload size limit")
        digest.update(chunk)
    stream.seek(0)
    return digest.hexdigest(), size


def create_document(
    session: Session,
    store: ObjectStore,
    stream: BinaryIO,
    filename: str,
    content_type: str,
    title: str,
    document_type: str,
    course_name: str | None,
    created_by: str,
    max_bytes: int,
) -> KnowledgeDocument:
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise ValueError("Unsupported document format")
    checksum, byte_size = _hash_stream(stream, max_bytes)
    if byte_size == 0:
        raise ValueError("Document must not be empty")
    document_id = str(uuid4())
    object_key = f"documents/{document_id}{suffix}"
    store.put(object_key, stream, byte_size, content_type or "application/octet-stream")
    document = KnowledgeDocumentModel(
        id=document_id,
        title=title.strip(),
        document_type=document_type.strip(),
        course_name=course_name.strip() if course_name else None,
        original_filename=filename,
        content_type=content_type or "application/octet-stream",
        object_key=object_key,
        checksum=checksum,
        byte_size=byte_size,
        status=DocumentStatus.uploaded.value,
        version=1,
        created_by=created_by,
    )
    session.add(document)
    session.commit()
    session.refresh(document)
    return KnowledgeDocument.model_validate(document)


def list_documents(session: Session, status: DocumentStatus | None = None) -> list[KnowledgeDocument]:
    statement = select(KnowledgeDocumentModel).order_by(KnowledgeDocumentModel.created_at.desc())
    if status:
        statement = statement.where(KnowledgeDocumentModel.status == status.value)
    return [KnowledgeDocument.model_validate(item) for item in session.scalars(statement).all()]


def get_document(session: Session, document_id: str) -> KnowledgeDocumentModel | None:
    return session.get(KnowledgeDocumentModel, document_id)


def transition_document(
    session: Session,
    document: KnowledgeDocumentModel,
    target_status: DocumentStatus,
    actor: str,
) -> KnowledgeDocument:
    current_status = DocumentStatus(document.status)
    if target_status not in TRANSITIONS[current_status]:
        raise ValueError(f"Cannot move document from {current_status.value} to {target_status.value}")
    document.status = target_status.value
    if target_status in {DocumentStatus.reviewed, DocumentStatus.published, DocumentStatus.rejected}:
        document.reviewed_by = actor
        document.reviewed_at = datetime.now(UTC)
    session.commit()
    session.refresh(document)
    return KnowledgeDocument.model_validate(document)

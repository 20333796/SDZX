from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.identity import Principal, Role, require_roles
from app.schemas import DocumentStatus, DocumentTransitionRequest, KnowledgeDocument, KnowledgeSearchResponse
from app.services.retrieval import search_published_knowledge
from app.services.knowledge import create_document, get_document, list_documents, transition_document
from app.storage import ObjectStoreError, get_object_store

router = APIRouter(prefix="/knowledge", tags=["knowledge"])
teaching_staff = require_roles(Role.teacher, Role.admin)


@router.get("/search", response_model=KnowledgeSearchResponse)
def search_knowledge(q: str, session: Session = Depends(get_db)) -> KnowledgeSearchResponse:
    return KnowledgeSearchResponse(citations=search_published_knowledge(session, q))


@router.get("/documents", response_model=list[KnowledgeDocument])
def get_documents(
    document_status: DocumentStatus | None = None,
    session: Session = Depends(get_db),
    principal: Principal = Depends(teaching_staff),
) -> list[KnowledgeDocument]:
    return list_documents(session, document_status)


@router.post("/documents", response_model=KnowledgeDocument, status_code=status.HTTP_201_CREATED)
def upload_document(
    title: str = Form(..., min_length=1, max_length=255),
    document_type: str = Form(..., min_length=1, max_length=80),
    course_name: str | None = Form(default=None, max_length=255),
    file: UploadFile = File(...),
    session: Session = Depends(get_db),
    principal: Principal = Depends(teaching_staff),
) -> KnowledgeDocument:
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="File name is required")
    try:
        return create_document(
            session,
            get_object_store(),
            file.file,
            file.filename,
            file.content_type or "application/octet-stream",
            title,
            document_type,
            course_name,
            principal.subject,
            get_settings().upload_max_bytes,
        )
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error
    except ObjectStoreError as error:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(error)) from error


@router.post("/documents/{document_id}/transitions", response_model=KnowledgeDocument)
def update_document_status(
    document_id: str,
    payload: DocumentTransitionRequest,
    session: Session = Depends(get_db),
    principal: Principal = Depends(teaching_staff),
) -> KnowledgeDocument:
    document = get_document(session, document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    try:
        return transition_document(session, document, payload.target_status, principal.subject)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error

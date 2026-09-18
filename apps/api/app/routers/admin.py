from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.identity import Role, require_roles
from app.schemas import ExternalResource, ExternalResourceCreate
from app.services.resources import create_resource

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post(
    "/external-resources",
    response_model=ExternalResource,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(Role.teacher, Role.admin))],
)
def add_external_resource(payload: ExternalResourceCreate, session: Session = Depends(get_db)) -> ExternalResource:
    try:
        return create_resource(session, payload)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error
    except IntegrityError as error:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Resource ID already exists") from error

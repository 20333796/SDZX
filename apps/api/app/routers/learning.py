from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.identity import Principal, Role, get_current_principal, require_roles
from app.schemas import (
    DiagnosisOverview,
    LearnerDiagnosis,
    LearningSubmission,
    LearningSubmissionCreate,
    LearningSubmissionFeedback,
    LearningTask,
    LearningTaskCreate,
)
from app.services.learning import (
    add_teacher_feedback,
    cohort_overview,
    create_learning_task,
    diagnose_learner,
    get_published_task,
    get_submission,
    list_learner_submissions,
    list_published_tasks,
    list_task_submissions,
    serialize_learning_task,
    submit_learning_task,
)

router = APIRouter(prefix="/learning", tags=["learning"])
teaching_staff = require_roles(Role.teacher, Role.admin)


@router.get("/tasks", response_model=list[LearningTask])
def get_learning_tasks(session: Session = Depends(get_db)) -> list[LearningTask]:
    return list_published_tasks(session)


@router.post("/tasks", response_model=LearningTask, status_code=status.HTTP_201_CREATED)
def add_learning_task(
    payload: LearningTaskCreate,
    session: Session = Depends(get_db),
    principal: Principal = Depends(teaching_staff),
) -> LearningTask:
    try:
        return create_learning_task(session, payload, principal.subject)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error
    except IntegrityError as error:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Learning task ID already exists") from error


@router.get("/tasks/{task_id}", response_model=LearningTask)
def get_learning_task(task_id: str, session: Session = Depends(get_db)) -> LearningTask:
    task = get_published_task(session, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Learning task not found")
    return serialize_learning_task(task)


@router.get("/tasks/{task_id}/submissions", response_model=list[LearningSubmission])
def get_task_submissions(
    task_id: str,
    session: Session = Depends(get_db),
    principal: Principal = Depends(teaching_staff),
) -> list[LearningSubmission]:
    return list_task_submissions(session, task_id)


@router.post("/tasks/{task_id}/submissions", response_model=LearningSubmission, status_code=status.HTTP_201_CREATED)
def create_learning_submission(
    task_id: str,
    payload: LearningSubmissionCreate,
    session: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
) -> LearningSubmission:
    try:
        return submit_learning_task(session, task_id, principal.subject, payload)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error


@router.get("/submissions/me", response_model=list[LearningSubmission])
def get_my_learning_submissions(
    session: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
) -> list[LearningSubmission]:
    return list_learner_submissions(session, principal.subject)


@router.post("/submissions/{submission_id}/feedback", response_model=LearningSubmission)
def create_teacher_feedback(
    submission_id: str,
    payload: LearningSubmissionFeedback,
    session: Session = Depends(get_db),
    principal: Principal = Depends(teaching_staff),
) -> LearningSubmission:
    submission = get_submission(session, submission_id)
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Learning submission not found")
    try:
        return add_teacher_feedback(session, submission, payload, principal.subject)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error


# ── 学情诊断 ────────────────────────────────────────────────

@router.get("/diagnosis/overview", response_model=DiagnosisOverview)
def get_diagnosis_overview(session: Session = Depends(get_db)) -> DiagnosisOverview:
    """班级学情总览：匿名聚合统计，可匿名访问。"""
    return cohort_overview(session)


@router.get("/diagnosis/{learner_id}", response_model=LearnerDiagnosis)
def get_learner_diagnosis(
    learner_id: str,
    session: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
) -> LearnerDiagnosis:
    """个人学情诊断：学员只能读自己的报告，教师与管理员可读全部。"""
    if principal.subject != learner_id and not ({Role.teacher, Role.admin} & set(principal.roles)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="只能查看本人的学情诊断")
    return diagnose_learner(session, learner_id)

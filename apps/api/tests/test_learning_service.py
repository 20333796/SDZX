from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database import Base
from app.schemas import LearningSubmissionCreate, LearningSubmissionFeedback
from app.services.learning import (
    add_teacher_feedback,
    get_submission,
    list_learner_submissions,
    list_published_tasks,
    seed_learning_tasks,
    submit_learning_task,
)


def test_learning_task_submission_and_teacher_feedback_form_auditable_loop() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        seed_learning_tasks(session)
        tasks = list_published_tasks(session)
        assert [task.id for task in tasks] == [
            "petroleum-system-evidence",
            "well-log-reservoir-evidence",
            "exploration-target-synthesis",
        ]

        submitted = submit_learning_task(
            session,
            "well-log-reservoir-evidence",
            "learner-001",
            LearningSubmissionCreate(response="2101-2102.5 m 为候选段，GR 低且 RT 较高。", evidence="需结合岩性和录井资料复核。"),
        )
        assert submitted.status.value == "submitted"

        model = get_submission(session, submitted.id)
        assert model is not None
        reviewed = add_teacher_feedback(
            session,
            model,
            LearningSubmissionFeedback(feedback="证据完整，请补充孔隙度曲线的解释。", score=88),
            "teacher-001",
        )
        assert reviewed.status.value == "reviewed"
        assert reviewed.score == 88
        assert reviewed.feedback_by == "teacher-001"
        assert list_learner_submissions(session, "learner-001")[0].id == submitted.id


def test_learning_submission_rejects_unavailable_task() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        seed_learning_tasks(session)
        try:
            submit_learning_task(session, "missing-task", "learner-001", LearningSubmissionCreate(response="answer"))
        except ValueError as error:
            assert "not available" in str(error)
        else:
            raise AssertionError("Unavailable tasks must reject submissions")

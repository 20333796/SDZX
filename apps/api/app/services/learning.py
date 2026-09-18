import json
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import LearningSubmissionModel, LearningTaskModel
from app.schemas import (
    CourseDiagnosis,
    DiagnosisOverview,
    LearnerDiagnosis,
    LearningSubmission,
    LearningSubmissionCreate,
    LearningSubmissionFeedback,
    LearningSubmissionStatus,
    LearningTask,
    LearningTaskCreate,
    LearningTaskStatus,
    TaskCohortStat,
)

DEFAULT_TASKS = (
    LearningTaskCreate(
        id="petroleum-system-evidence",
        title="油气成藏证据链",
        summary="从课程资料中组织烃源岩、储层、盖层与圈闭之间的关系。",
        course_name="油矿地质学",
        objective="使用至少三类地质证据解释一个油气成藏系统。",
        instructions=["选择一个盆地或课程案例。", "列出烃源岩、储层、盖层和圈闭的证据。", "说明仍需补充的数据与不确定性。"],
        estimated_minutes=40,
        difficulty="基础",
        status=LearningTaskStatus.published,
        sort_order=10,
    ),
    LearningTaskCreate(
        id="well-log-reservoir-evidence",
        title="测井曲线储层判识",
        summary="结合 GR、RT 和 NPHI 曲线完成教学井段的候选储层判识。",
        course_name="地球物理测井",
        objective="给出候选井段、判识依据和至少一项需要复核的地质证据。",
        instructions=["打开测井智能解释教学案例。", "记录候选段的曲线响应。", "说明岩性或录井资料为何需要共同复核。"],
        estimated_minutes=30,
        difficulty="进阶",
        status=LearningTaskStatus.published,
        sort_order=20,
    ),
    LearningTaskCreate(
        id="exploration-target-synthesis",
        title="勘探目标综合评价",
        summary="将课程资源、构造背景和风险因素整理为可追溯的勘探目标说明。",
        course_name="油气田勘探",
        objective="形成包含目标、证据、风险与下一步资料需求的简短说明。",
        instructions=["定义勘探目标和研究范围。", "区分支持目标的证据与主要风险。", "提出下一步需要的资料或验证方法。"],
        estimated_minutes=45,
        difficulty="进阶",
        status=LearningTaskStatus.published,
        sort_order=30,
    ),
)


def serialize_learning_task(model: LearningTaskModel) -> LearningTask:
    return LearningTask(
        id=model.id,
        title=model.title,
        summary=model.summary,
        course_name=model.course_name,
        objective=model.objective,
        instructions=json.loads(model.instructions_json),
        estimated_minutes=model.estimated_minutes,
        difficulty=model.difficulty,
        status=LearningTaskStatus(model.status),
        sort_order=model.sort_order,
    )


def _submission(model: LearningSubmissionModel) -> LearningSubmission:
    return LearningSubmission(
        id=model.id,
        task_id=model.task_id,
        learner_id=model.learner_id,
        response=model.response,
        evidence=model.evidence,
        status=LearningSubmissionStatus(model.status),
        score=model.score,
        feedback=model.feedback,
        feedback_by=model.feedback_by,
        feedback_at=model.feedback_at,
        submitted_at=model.submitted_at,
    )


def seed_learning_tasks(session: Session) -> None:
    if session.scalar(select(LearningTaskModel.id).limit(1)):
        return
    session.add_all(
        LearningTaskModel(
            id=task.id,
            title=task.title,
            summary=task.summary,
            course_name=task.course_name,
            objective=task.objective,
            instructions_json=json.dumps(task.instructions, ensure_ascii=False),
            estimated_minutes=task.estimated_minutes,
            difficulty=task.difficulty,
            status=task.status.value,
            sort_order=task.sort_order,
        )
        for task in DEFAULT_TASKS
    )
    session.commit()


def list_published_tasks(session: Session) -> list[LearningTask]:
    statement = (
        select(LearningTaskModel)
        .where(LearningTaskModel.status == LearningTaskStatus.published.value)
        .order_by(LearningTaskModel.sort_order, LearningTaskModel.title)
    )
    return [serialize_learning_task(task) for task in session.scalars(statement).all()]


def get_published_task(session: Session, task_id: str) -> LearningTaskModel | None:
    task = session.get(LearningTaskModel, task_id)
    if task and task.status == LearningTaskStatus.published.value:
        return task
    return None


def create_learning_task(session: Session, payload: LearningTaskCreate, actor: str) -> LearningTask:
    text_fields = (payload.id, payload.title, payload.summary, payload.course_name, payload.objective, payload.difficulty)
    if not all(field.strip() for field in text_fields) or not all(instruction.strip() for instruction in payload.instructions):
        raise ValueError("Learning task fields and instructions must not be blank")
    task = LearningTaskModel(
        id=payload.id,
        title=payload.title.strip(),
        summary=payload.summary.strip(),
        course_name=payload.course_name.strip(),
        objective=payload.objective.strip(),
        instructions_json=json.dumps(payload.instructions, ensure_ascii=False),
        estimated_minutes=payload.estimated_minutes,
        difficulty=payload.difficulty.strip(),
        status=payload.status.value,
        sort_order=payload.sort_order,
        created_by=actor,
    )
    session.add(task)
    session.commit()
    session.refresh(task)
    return serialize_learning_task(task)


def submit_learning_task(
    session: Session,
    task_id: str,
    learner_id: str,
    payload: LearningSubmissionCreate,
) -> LearningSubmission:
    if not get_published_task(session, task_id):
        raise ValueError("Learning task is not available")
    response = payload.response.strip()
    if not response:
        raise ValueError("Submission response is required")
    submission = LearningSubmissionModel(
        id=str(uuid4()),
        task_id=task_id,
        learner_id=learner_id,
        response=response,
        evidence=payload.evidence.strip() if payload.evidence else None,
        status=LearningSubmissionStatus.submitted.value,
    )
    session.add(submission)
    session.commit()
    session.refresh(submission)
    return _submission(submission)


def list_learner_submissions(session: Session, learner_id: str) -> list[LearningSubmission]:
    statement = (
        select(LearningSubmissionModel)
        .where(LearningSubmissionModel.learner_id == learner_id)
        .order_by(LearningSubmissionModel.submitted_at.desc())
    )
    return [_submission(submission) for submission in session.scalars(statement).all()]


def list_task_submissions(session: Session, task_id: str) -> list[LearningSubmission]:
    statement = (
        select(LearningSubmissionModel)
        .where(LearningSubmissionModel.task_id == task_id)
        .order_by(LearningSubmissionModel.submitted_at.desc())
    )
    return [_submission(submission) for submission in session.scalars(statement).all()]


def get_submission(session: Session, submission_id: str) -> LearningSubmissionModel | None:
    return session.get(LearningSubmissionModel, submission_id)


def add_teacher_feedback(
    session: Session,
    submission: LearningSubmissionModel,
    payload: LearningSubmissionFeedback,
    teacher_id: str,
) -> LearningSubmission:
    feedback = payload.feedback.strip()
    if not feedback:
        raise ValueError("Feedback is required")
    submission.feedback = feedback
    submission.score = payload.score
    submission.feedback_by = teacher_id
    submission.feedback_at = datetime.now(UTC)
    submission.status = LearningSubmissionStatus.reviewed.value
    session.commit()
    session.refresh(submission)
    return _submission(submission)


# ── 学情诊断 ────────────────────────────────────────────────

def _round1(value: float | None) -> float | None:
    return round(value, 1) if value is not None else None


def cohort_overview(session: Session) -> DiagnosisOverview:
    """班级学情总览：按任务聚合提交数、复核数与均分，不携带学员身份。"""
    from app.models import LearningSubmissionModel

    tasks = session.scalars(
        select(LearningTaskModel)
        .where(LearningTaskModel.status == LearningTaskStatus.published.value)
        .order_by(LearningTaskModel.sort_order, LearningTaskModel.title)
    ).all()
    per_task: list[TaskCohortStat] = []
    submissions_total = 0
    reviewed_total = 0
    score_sum = 0.0
    score_count = 0
    for task in tasks:
        submissions = session.scalars(
            select(LearningSubmissionModel).where(LearningSubmissionModel.task_id == task.id)
        ).all()
        scores = [item.score for item in submissions if item.status == LearningSubmissionStatus.reviewed.value and item.score is not None]
        per_task.append(
            TaskCohortStat(
                task_id=task.id,
                title=task.title,
                course_name=task.course_name,
                difficulty=task.difficulty,
                submissions=len(submissions),
                reviewed=sum(1 for item in submissions if item.status == LearningSubmissionStatus.reviewed.value),
                avg_score=_round1(sum(scores) / len(scores)) if scores else None,
            )
        )
        submissions_total += len(submissions)
        reviewed_total += len(scores) + sum(1 for item in submissions if item.status == LearningSubmissionStatus.reviewed.value and item.score is None)
        score_sum += sum(scores)
        score_count += len(scores)
    return DiagnosisOverview(
        tasks_total=len(tasks),
        submissions_total=submissions_total,
        reviewed_total=reviewed_total,
        avg_score=_round1(score_sum / score_count) if score_count else None,
        per_task=per_task,
    )


def diagnose_learner(session: Session, learner_id: str) -> LearnerDiagnosis:
    """个人学情诊断：规则化生成，可由教师复核，不虚构 AI 结论。"""
    from app.models import LearningSubmissionModel

    published = session.scalars(
        select(LearningTaskModel).where(LearningTaskModel.status == LearningTaskStatus.published.value)
    ).all()
    task_index = {task.id: task for task in published}
    submissions = session.scalars(
        select(LearningSubmissionModel).where(LearningSubmissionModel.learner_id == learner_id)
    ).all()

    grouped: dict[str, list[LearningSubmissionModel]] = {}
    for item in submissions:
        if item.task_id in task_index:
            grouped.setdefault(item.task_id, []).append(item)

    courses: list[CourseDiagnosis] = []
    score_sum = 0.0
    score_count = 0
    reviewed_total = 0
    pending_review = 0
    for task_id, items in grouped.items():
        task = task_index[task_id]
        scores = [item.score for item in items if item.status == LearningSubmissionStatus.reviewed.value and item.score is not None]
        reviewed = sum(1 for item in items if item.status == LearningSubmissionStatus.reviewed.value)
        reviewed_total += reviewed
        pending_review += len(items) - reviewed
        avg = sum(scores) / len(scores) if scores else None
        if avg is not None:
            score_sum += avg * len(scores)
            score_count += len(scores)
        if avg is None:
            level = "待巩固"
        elif avg >= 85:
            level = "扎实"
        elif avg >= 70:
            level = "待巩固"
        else:
            level = "需加强"
        courses.append(
            CourseDiagnosis(
                course_name=task.course_name,
                attempts=len(items),
                reviewed=reviewed,
                avg_score=_round1(avg),
                level=level,
            )
        )
    courses.sort(key=lambda item: (["扎实", "待巩固", "需加强"].index(item.level), item.course_name))

    coverage = len(grouped) / len(published) if published else 0.0
    overall_avg = score_sum / score_count if score_count else None
    strengths = [f"{item.course_name}：已复核均分 {item.avg_score}，判识结论可复核" for item in courses if item.level == "扎实"]
    focus = [
        f"{item.course_name}：均分 {item.avg_score}，建议重做「{task_index[[key for key, value in grouped.items() if value and task_index[key].course_name == item.course_name][0]].title}」并补全判识依据"
        if any(task_index[key].course_name == item.course_name for key in grouped)
        else f"{item.course_name}：建议从已发布任务入手"
        for item in courses
        if item.level == "需加强"
    ]
    suggestions: list[str] = []
    if pending_review:
        suggestions.append(f"有 {pending_review} 份提交待教师复核，复核通过后才计入能力证据。")
    if coverage < 0.5 and published:
        first = min(published, key=lambda task: task.sort_order)
        suggestions.append(f"任务覆盖 {len(grouped)}/{len(published)}，建议先完成「{first.title}」建立基线。")
    if overall_avg is not None and overall_avg < 70:
        suggestions.append("整体均分偏低：优先核对判识依据中的引用来源，再对照任务目标逐条自检。")
    if not suggestions:
        suggestions.append("保持当前节奏：完成任务后补充判识依据，等待教师复核即可。")
    return LearnerDiagnosis(
        learner_id=learner_id,
        published_tasks=len(published),
        attempts=len(submissions),
        reviewed=reviewed_total,
        avg_score=_round1(overall_avg),
        coverage=round(coverage, 2),
        courses=courses,
        strengths=strengths,
        focus=focus,
        suggestions=suggestions,
    )


DEMO_SUBMISSIONS: list[dict] = [
    {"task_id": "petroleum-system-evidence", "learner_id": "demo-learner-01", "status": "reviewed", "score": 88, "response": "以烃源岩厚度与镜质体反射率圈定有效生烃区。", "evidence": "课程图谱-烃源岩；教材图 4-12", "feedback": "证据链完整，结论可靠。"},
    {"task_id": "well-log-reservoir-evidence", "learner_id": "demo-learner-01", "status": "reviewed", "score": 76, "response": "用声波-密度交会划分储层段并计算孔隙度。", "evidence": "测井响应机理卡片", "feedback": "孔隙度计算正确，需补渗透率依据。"},
    {"task_id": "exploration-target-synthesis", "learner_id": "demo-learner-02", "status": "reviewed", "score": 64, "response": "综合圈闭与盖层条件给出目标排序。", "evidence": "圈闭知识点", "feedback": "运移路径未考虑，排序依据不足。"},
    {"task_id": "petroleum-system-evidence", "learner_id": "demo-learner-02", "status": "reviewed", "score": 58, "response": "生烃强度计算遗漏厚度校正。", "evidence": "仅引用课件一页", "feedback": "依据单薄，需重做。"},
    {"task_id": "well-log-reservoir-evidence", "learner_id": "demo-learner-02", "status": "submitted", "score": None, "response": "电阻率曲线识别油水界面。", "evidence": "电阻率测井知识点", "feedback": None},
    {"task_id": "well-log-reservoir-evidence", "learner_id": "demo-learner-03", "status": "reviewed", "score": 91, "response": "三孔隙度交会+阿尔奇公式联立求饱和度。", "evidence": "阿尔奇公式；孔隙度测井系列", "feedback": "方法选择得当，可作范例。"},
]


def seed_demo_submissions(session: Session) -> None:
    """教师复核流程演示用的示例提交（learner_id 以 demo- 前缀标识，可在总览页明示）。"""
    from app.models import LearningSubmissionModel

    if session.scalar(select(LearningSubmissionModel.id).limit(1)):
        return
    session.add_all(
        LearningSubmissionModel(
            id=uuid4().hex,
            task_id=item["task_id"],
            learner_id=item["learner_id"],
            response=item["response"],
            evidence=item["evidence"],
            status=item["status"],
            score=item["score"],
            feedback=item["feedback"],
        )
        for item in DEMO_SUBMISSIONS
    )
    session.commit()

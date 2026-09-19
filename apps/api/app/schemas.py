from enum import Enum
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class ResourceCategory(str, Enum):
    courses = "courses"
    knowledge = "knowledge"
    practice = "practice"


class ResourceStatus(str, Enum):
    active = "active"
    pending = "pending"


class ExternalResource(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    title: str
    provider: str
    category: ResourceCategory
    course_level: str
    audience: str
    credits: float | None = None
    language: str = "中文"
    status: ResourceStatus = ResourceStatus.active
    url: HttpUrl | None = None
    cover_asset: str | None = None
    description: str
    sort_order: int


class ExternalResourceCreate(BaseModel):
    id: str
    title: str
    provider: str
    category: ResourceCategory
    course_level: str
    audience: str
    credits: float | None = None
    language: str = "中文"
    status: ResourceStatus = ResourceStatus.active
    url: HttpUrl | None = None
    cover_asset: str | None = None
    description: str
    sort_order: int = 0


class ChatRequest(BaseModel):
    mode: Literal["conversation", "search", "inquiry"] = "conversation"
    message: str
    conversation_id: str | None = None


class ClickEvent(BaseModel):
    source: str = "resource_catalog"


class DocumentStatus(str, Enum):
    uploaded = "uploaded"
    parsed = "parsed"
    reviewed = "reviewed"
    indexed = "indexed"
    published = "published"
    rejected = "rejected"


class KnowledgeDocument(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    title: str
    document_type: str
    course_name: str | None = None
    original_filename: str
    content_type: str
    checksum: str
    byte_size: int
    status: DocumentStatus
    version: int
    created_by: str
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None
    parsing_attempts: int
    processing_error: str | None = None
    parsed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class DocumentTransitionRequest(BaseModel):
    target_status: DocumentStatus


class Citation(BaseModel):
    document_id: str
    title: str
    course_name: str | None = None
    source_locator: str | None = None
    excerpt: str
    score: float


class ChatResourceReference(BaseModel):
    """A portal resource surfaced alongside an answer."""

    id: str
    title: str
    category: Literal["courses", "practice", "mentor"]
    provider: str | None = None
    description: str
    url: str | None = None
    embedded_url: str | None = None
    route: str | None = None


class KnowledgeSearchResponse(BaseModel):
    citations: list[Citation]


class KnowledgeGraphNode(BaseModel):
    id: str
    name: str
    category: str
    description: str


class KnowledgeGraphEdge(BaseModel):
    source: str
    target: str
    relation: str


class KnowledgeGraphResponse(BaseModel):
    nodes: list[KnowledgeGraphNode]
    edges: list[KnowledgeGraphEdge]


class PortalNavigationLink(BaseModel):
    label: str
    target: str
    category: ResourceCategory | None = None


class PortalNavigationGroup(BaseModel):
    title: str
    links: list[PortalNavigationLink]


class PortalStat(BaseModel):
    value: str
    label: str


class PortalConfig(BaseModel):
    navigation: list[PortalNavigationGroup]
    stats: list[PortalStat]


class LearningTaskStatus(str, Enum):
    draft = "draft"
    published = "published"


class LearningSubmissionStatus(str, Enum):
    submitted = "submitted"
    reviewed = "reviewed"


class LearningTask(BaseModel):
    id: str
    title: str
    summary: str
    course_name: str
    objective: str
    instructions: list[str]
    estimated_minutes: int
    difficulty: str
    status: LearningTaskStatus
    sort_order: int


class LearningTaskCreate(BaseModel):
    id: str = Field(min_length=1, max_length=120)
    title: str = Field(min_length=1, max_length=255)
    summary: str = Field(min_length=1, max_length=4000)
    course_name: str = Field(min_length=1, max_length=255)
    objective: str = Field(min_length=1, max_length=4000)
    instructions: list[str] = Field(min_length=1, max_length=8)
    estimated_minutes: int = Field(ge=5, le=240)
    difficulty: str = Field(min_length=1, max_length=32)
    status: LearningTaskStatus = LearningTaskStatus.draft
    sort_order: int = 0


class LearningSubmissionCreate(BaseModel):
    response: str = Field(min_length=1, max_length=20_000)
    evidence: str | None = Field(default=None, max_length=10_000)


class LearningSubmissionFeedback(BaseModel):
    feedback: str = Field(min_length=1, max_length=10_000)
    score: float | None = Field(default=None, ge=0, le=100)


class LearningSubmission(BaseModel):
    id: str
    task_id: str
    learner_id: str
    response: str
    evidence: str | None = None
    status: LearningSubmissionStatus
    score: float | None = None
    feedback: str | None = None
    feedback_by: str | None = None
    feedback_at: datetime | None = None
    submitted_at: datetime


class GeoDatasetCategory(str, Enum):
    geology = "geology"
    borehole = "borehole"
    logging = "logging"
    seismic = "seismic"
    geochemistry = "geochemistry"
    remote_sensing = "remote_sensing"
    terrain = "terrain"
    potential_field = "potential_field"


class GeoDatasetFeature(BaseModel):
    """数据集内公开的示例点位（教学示意，非工业成果）。"""

    name: str
    lon: float = Field(ge=73, le=136)
    lat: float = Field(ge=3, le=54)
    value: str | None = None
    note: str | None = None


class GeoDataset(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    title: str
    category: GeoDatasetCategory
    region: str
    description: str
    data_format: str
    resolution: str
    size_label: str
    source: str
    license: str
    access_url: str | None = None
    sort_order: int
    feature_count: int = 0


class GeoDatasetDetail(GeoDataset):
    features: list[GeoDatasetFeature] = []


class GeoDatasetStats(BaseModel):
    total: int
    categories: int
    regions: int
    by_category: dict[str, int]


class KnowledgeGraphNeighbor(BaseModel):
    id: str
    name: str
    category: str
    relation: str
    direction: Literal["out", "in"]


class KnowledgeGraphNodeDetail(KnowledgeGraphNode):
    neighbors: list[KnowledgeGraphNeighbor] = []


class KnowledgeGraphStats(BaseModel):
    total: int
    by_category: dict[str, int]
    relations: int


class TaskCohortStat(BaseModel):
    task_id: str
    title: str
    course_name: str
    difficulty: str
    submissions: int
    reviewed: int
    avg_score: float | None = None


class DiagnosisOverview(BaseModel):
    """班级学情总览：只聚合匿名统计，不含任何学员身份。"""

    tasks_total: int
    submissions_total: int
    reviewed_total: int
    avg_score: float | None = None
    per_task: list[TaskCohortStat]


class CourseDiagnosis(BaseModel):
    course_name: str
    attempts: int
    reviewed: int
    avg_score: float | None = None
    level: Literal["扎实", "待巩固", "需加强"]


class LearnerDiagnosis(BaseModel):
    learner_id: str
    published_tasks: int
    attempts: int
    reviewed: int
    avg_score: float | None = None
    coverage: float
    courses: list[CourseDiagnosis]
    strengths: list[str]
    focus: list[str]
    suggestions: list[str]

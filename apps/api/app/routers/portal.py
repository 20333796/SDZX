from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ExternalResourceModel, LearningTaskModel
from app.schemas import PortalConfig, PortalNavigationGroup, PortalNavigationLink, PortalStat, ResourceCategory

router = APIRouter(prefix="/portal-config", tags=["portal"])

DEFAULT_PORTAL_CONFIG = PortalConfig(
    navigation=[
        PortalNavigationGroup(
            title="知源智汇",
            links=[
                PortalNavigationLink(label="AI智慧课程", target="resources", category=ResourceCategory.courses),
                PortalNavigationLink(label="学科知识图谱", target="knowledge-graph"),
                PortalNavigationLink(label="地学数据", target="geo-data"),
            ],
        ),
        PortalNavigationGroup(
            title="因材智教",
            links=[
                PortalNavigationLink(label="学情诊断", target="learning-diagnosis"),
                PortalNavigationLink(label="智能研学", target="learning-tasks"),
                PortalNavigationLink(label="导师图谱", target="mentor-graph"),
            ],
        ),
        PortalNavigationGroup(
            title="实践智导",
            links=[
                PortalNavigationLink(label="虚拟仿真", target="practice-simulation"),
                PortalNavigationLink(label="野外实训", target="field-training"),
                PortalNavigationLink(label="工程案例", target="case-library"),
            ],
        ),
        PortalNavigationGroup(
            title="能力智验",
            links=[
                PortalNavigationLink(label="地学智能设计", target="geology-design"),
                PortalNavigationLink(label="独立能力测评", target="capability-assessment"),
                PortalNavigationLink(label="成长画像", target="learning-profile"),
            ],
        ),
    ],
    stats=[
        PortalStat(value="12+", label="课程资源"),
        PortalStat(value="03", label="学习路径"),
        PortalStat(value="试运行", label="开放状态"),
    ],
)


@router.get("", response_model=PortalConfig)
def get_portal_config(session: Session = Depends(get_db)) -> PortalConfig:
    """Return anonymous-safe navigation and homepage status information."""
    resource_count = session.scalar(select(func.count()).select_from(ExternalResourceModel)) or 0
    learning_path_count = session.scalar(
        select(func.count()).select_from(LearningTaskModel).where(LearningTaskModel.status == "published")
    ) or 0
    return DEFAULT_PORTAL_CONFIG.model_copy(
        update={
            "stats": [
                PortalStat(value=f"{resource_count}+", label="课程资源"),
                PortalStat(value=f"{learning_path_count:02d}", label="学习路径"),
                PortalStat(value="试运行", label="开放状态"),
            ]
        }
    )

import asyncio

from app.config import Settings
from app.schemas import ChatRequest, ChatResourceReference, Citation
from app.services.llm import generate_grounded_answer


def test_unconfigured_model_uses_grounded_retrieval_guidance() -> None:
    answer = asyncio.run(
        generate_grounded_answer(
            Settings(),
            ChatRequest(message="如何识别储层"),
            [
                Citation(
                    document_id="document-1",
                    title="油矿地质学讲义",
                    source_locator="chunk:1",
                    excerpt="GR、RT 和孔隙度曲线需要结合解释。",
                    score=1.0,
                )
            ],
        )
    )
    assert "油矿地质学讲义" in answer


def test_fallback_course_recommendation_includes_official_address() -> None:
    answer = asyncio.run(
        generate_grounded_answer(
            Settings(),
            ChatRequest(mode="search", message="推荐课程"),
            [],
            [
                ChatResourceReference(
                    id="course-1",
                    title="油矿地质学",
                    category="courses",
                    description="课程入口",
                    url="https://higher.smartedu.cn/course/1",
                )
            ],
        )
    )
    assert "[油矿地质学](https://higher.smartedu.cn/course/1)" in answer

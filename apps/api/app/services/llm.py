import httpx

from app.config import Settings
from app.schemas import ChatRequest, ChatResourceReference, Citation


def _resource_links(resources: list[ChatResourceReference] | None) -> str:
    links = []
    for resource in resources or []:
        if resource.url:
            links.append(f"- [{resource.title}]({resource.url})")
        else:
            links.append(f"- {resource.title}：暂无可用访问地址")
    return "\n".join(links)


def build_fallback_answer(
    request: ChatRequest,
    citations: list[Citation],
    resources: list[ChatResourceReference] | None = None,
) -> str:
    if not citations:
        answer = "当前没有可引用的已发布课程资料。请先从课程资源或教师审核后的资料开始，并说明你希望分析的地质对象、数据类型和学习目标。"
    else:
        excerpts = "\n".join(f"- {citation.title}：{citation.excerpt}" for citation in citations)
        answer = f"已检索到与“{request.message}”相关的课程资料。请先核对以下证据，再结合课程任务完成判断：\n{excerpts}"
    links = _resource_links(resources)
    if links:
        answer += f"\n\n可直接访问的课程与资源：\n{links}"
    return answer


async def generate_grounded_answer(
    settings: Settings,
    request: ChatRequest,
    citations: list[Citation],
    resources: list[ChatResourceReference] | None = None,
) -> str:
    if not settings.llm_enabled:
        return build_fallback_answer(request, citations, resources)
    context = "\n\n".join(
        f"来源：{citation.title}（{citation.source_locator or '未标注位置'}）\n内容：{citation.excerpt}"
        for citation in citations
    ) or "没有可用的已发布资料。请说明资料不足，不要编造事实。"
    resource_context = "\n".join(
        f"- {resource.title}：{resource.url or '暂无可用访问地址'}" for resource in resources or []
    ) or "没有检索到可直接访问的课程或资源。"
    messages = [
        {
            "role": "system",
            "content": "你是中国石油大学（北京）地质资源与地质工程学科教育助手。只依据提供的课程资料回答；资料不足时明确说明。回答用简体中文，解释地质依据，不给出生产决策结论。推荐课程、课程资源或仿真平台时，每条必须使用检索到的官方地址输出 Markdown 链接 [名称](URL)；没有地址就写暂无可用访问地址，禁止编造 URL。",
        },
        {"role": "user", "content": f"问题：{request.message}\n\n课程资料：\n{context}\n\n可推荐资源及官方地址：\n{resource_context}"},
    ]
    try:
        async with httpx.AsyncClient(timeout=settings.llm_timeout_seconds) as client:
            response = await client.post(
                f"{settings.ollama_base_url.rstrip('/')}/api/chat",
                json={"model": settings.ollama_model, "messages": messages, "stream": False},
            )
            response.raise_for_status()
            content = response.json().get("message", {}).get("content", "").strip()
            if content:
                links = _resource_links(resources)
                return f"{content}\n\n可直接访问的课程与资源：\n{links}" if links else content
    except (httpx.HTTPError, ValueError, AttributeError):
        pass
    return build_fallback_answer(request, citations, resources)

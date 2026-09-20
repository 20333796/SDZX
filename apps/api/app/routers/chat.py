import asyncio
import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import get_settings
from app.schemas import ChatRequest
from app.services.llm import generate_grounded_answer
from app.services.retrieval import search_portal_resources, search_published_knowledge

router = APIRouter(prefix="/chat", tags=["chat"])


def build_reply(request: ChatRequest, has_citations: bool = False) -> str:
    replies = {
        "conversation": "我会优先依据已审核的地质课程资料回答，并在正式知识库接入后标明课程与章节来源。",
        "search": "已为你整理相关课程、知识图谱和实验资源。可以从油矿地质学、油气田勘探或测井反演与信息处理开始。",
        "inquiry": "我们从证据开始：先观察岩性与测井曲线特征，再判断储层条件，最后说明每一步的地质依据。",
    }
    citation_note = "以下内容引用已发布课程资料。" if has_citations else "当前没有可引用的已发布课程资料，以下为学习引导。"
    return f"关于“{request.message}”，{replies[request.mode]}{citation_note}"


@router.post("/stream")
async def stream_chat(request: ChatRequest, session: Session = Depends(get_db)) -> StreamingResponse:
    async def event_source():
        citations = search_published_knowledge(session, request.message)
        resources = search_portal_resources(session, request.message)
        reply = await generate_grounded_answer(get_settings(), request, citations, resources)
        for token in reply:
            yield f"event: token\ndata: {json.dumps({'content': token}, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0.012)
        yield f"event: sources\ndata: {json.dumps({'citations': [citation.model_dump() for citation in citations]}, ensure_ascii=False)}\n\n"
        yield f"event: resources\ndata: {json.dumps({'resources': [resource.model_dump() for resource in resources]}, ensure_ascii=False)}\n\n"
        yield "event: complete\ndata: {}\n\n"

    return StreamingResponse(event_source(), media_type="text/event-stream")

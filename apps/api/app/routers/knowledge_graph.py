from fastapi import APIRouter, HTTPException, Query, status

from app.data_kg import COURSE_GRAPH
from app.schemas import KnowledgeGraphNeighbor, KnowledgeGraphNodeDetail, KnowledgeGraphResponse, KnowledgeGraphStats

router = APIRouter(prefix="/knowledge-graph", tags=["knowledge-graph"])

NODE_INDEX = {node.id: node for node in COURSE_GRAPH.nodes}


def _filtered_graph(category: str | None) -> KnowledgeGraphResponse:
    if not category:
        return COURSE_GRAPH
    nodes = [node for node in COURSE_GRAPH.nodes if node.category == category]
    allowed = {node.id for node in nodes}
    edges = [edge for edge in COURSE_GRAPH.edges if edge.source in allowed and edge.target in allowed]
    return KnowledgeGraphResponse(nodes=nodes, edges=edges)


@router.get("", response_model=KnowledgeGraphResponse)
def get_knowledge_graph(
    category: str | None = Query(default=None, max_length=12),
) -> KnowledgeGraphResponse:
    return _filtered_graph(category)


@router.get("/stats", response_model=KnowledgeGraphStats)
def get_knowledge_graph_stats() -> KnowledgeGraphStats:
    by_category: dict[str, int] = {}
    for node in COURSE_GRAPH.nodes:
        by_category[node.category] = by_category.get(node.category, 0) + 1
    return KnowledgeGraphStats(total=len(COURSE_GRAPH.nodes), by_category=by_category, relations=len(COURSE_GRAPH.edges))


@router.get("/node/{node_id}", response_model=KnowledgeGraphNodeDetail)
def get_knowledge_graph_node(node_id: str) -> KnowledgeGraphNodeDetail:
    node = NODE_INDEX.get(node_id)
    if not node:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge node not found")
    neighbors: list[KnowledgeGraphNeighbor] = []
    for edge in COURSE_GRAPH.edges:
        if edge.source == node_id:
            target = NODE_INDEX.get(edge.target)
            if target:
                neighbors.append(KnowledgeGraphNeighbor(id=target.id, name=target.name, category=target.category, relation=edge.relation, direction="out"))
        elif edge.target == node_id:
            source = NODE_INDEX.get(edge.source)
            if source:
                neighbors.append(KnowledgeGraphNeighbor(id=source.id, name=source.name, category=source.category, relation=edge.relation, direction="in"))
    return KnowledgeGraphNodeDetail(**node.model_dump(), neighbors=neighbors)

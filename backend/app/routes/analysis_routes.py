from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Dict, Any, List
from ..services.ast_service import parse_ast

router = APIRouter(tags=["analysis"])

class ASTRequest(BaseModel):
    code: str = Field(..., min_length=1)
    language: str = Field(default="python")

@router.post("/ast-graph")
def get_ast_graph(payload: ASTRequest):
    ast_data = parse_ast(payload.language, payload.code)
    
    nodes = []
    edges = []
    
    # Flatten hierarchical AST into nodes and edges
    def traverse(node: Dict[str, Any], parent_id: str = None):
        node_id = str(len(nodes) + 1)
        nodes.append({
            "id": node_id,
            "data": {"label": node.get("type", "Unknown")},
            "position": {"x": 0, "y": 0} # frontend will apply layout engine
        })
        
        if parent_id:
            edges.append({
                "id": f"e{parent_id}-{node_id}",
                "source": parent_id,
                "target": node_id
            })
            
        for child in node.get("children", []):
            traverse(child, node_id)
            
    traverse(ast_data)
    
    return {"nodes": nodes, "edges": edges}


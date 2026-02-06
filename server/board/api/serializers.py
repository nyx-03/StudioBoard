from __future__ import annotations

from typing import Any, Dict, List

from ..models import Board, Column, Idea


def serialize_board(board: Board) -> Dict[str, Any]:
    return {"id": board.id, "name": board.name}


def serialize_tag_names(idea: Idea) -> List[str]:
    if hasattr(idea, "tags"):
        try:
            return [t.name for t in idea.tags.all()]
        except Exception:
            return []
    return []


def serialize_column_min(column: Column) -> Dict[str, Any]:
    return {"id": column.id, "name": column.name}


def serialize_idea_card(idea: Idea) -> Dict[str, Any]:
    """
    Format léger pour les listes/kanban.
    """
    return {
        "id": idea.id,
        "title": idea.title,
        "status": getattr(idea, "status", None),
        "impact": getattr(idea, "impact", None),
        "next_action": getattr(idea, "next_action", None),
        "updated_at": idea.updated_at.isoformat() if getattr(idea, "updated_at", None) else None,
        "tags": serialize_tag_names(idea),
        **({"position": idea.position} if hasattr(idea, "position") else {}),
    }


def serialize_idea_detail(idea: Idea) -> Dict[str, Any]:
    """
    Format complet pour la page détail / édition.
    """
    data = {
        "id": idea.id,
        "title": idea.title,
        "body_md": getattr(idea, "body_md", ""),
        "status": getattr(idea, "status", None),
        "impact": getattr(idea, "impact", None),
        "next_action": getattr(idea, "next_action", None),
        "column": serialize_column_min(idea.column) if hasattr(idea, "column") and idea.column_id else None,
        "tags": serialize_tag_names(idea),
        "created_at": idea.created_at.isoformat() if getattr(idea, "created_at", None) else None,
        "updated_at": idea.updated_at.isoformat() if getattr(idea, "updated_at", None) else None,
    }
    if hasattr(idea, "position"):
        data["position"] = idea.position
    return data

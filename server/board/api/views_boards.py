from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET

from .responses import json_nostore, require_auth
from ..models import Board, Column, Idea


@require_GET
def boards_list_api(request):
    if not request.user.is_authenticated:
        return json_nostore({"boards": []})

    boards = Board.objects.order_by("id").values("id", "name")
    return json_nostore({"boards": list(boards)})


@require_GET
def board_kanban_api(request, board_id):
    err = require_auth(request)
    if err:
        return err

    board = get_object_or_404(Board, id=board_id)

    columns_qs = Column.objects.filter(board=board).order_by("order", "id")
    ideas_qs = (
        Idea.objects.filter(column__board=board)
        .select_related("column")
        .prefetch_related("tags")
    )

    if hasattr(Idea, "position"):
        ideas_qs = ideas_qs.order_by("column_id", "position", "id")
    else:
        ideas_qs = ideas_qs.order_by("column_id", "id")

    ideas_by_col = {}
    for idea in ideas_qs:
        ideas_by_col.setdefault(idea.column_id, []).append(
            {
                "id": idea.id,
                "title": idea.title,
                "status": getattr(idea, "status", None),
                "impact": getattr(idea, "impact", None),
                "next_action": getattr(idea, "next_action", None),
                "updated_at": idea.updated_at.isoformat() if getattr(idea, "updated_at", None) else None,
                "tags": [t.name for t in idea.tags.all()] if hasattr(idea, "tags") else [],
            }
        )

    columns = []
    for col in columns_qs:
        columns.append(
            {
                "id": col.id,
                "name": col.name,
                "order": getattr(col, "order", None),
                "ideas": ideas_by_col.get(col.id, []),
            }
        )

    return json_nostore({"board": {"id": board.id, "name": board.name}, "columns": columns})
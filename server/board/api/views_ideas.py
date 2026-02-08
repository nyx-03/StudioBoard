from __future__ import annotations

from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET, require_POST
from .debug import debug_log
from .parsing import parse_payload, get_int
from .responses import json_nostore, require_auth
from .serializers import (
    serialize_board,
    serialize_idea_card,
    serialize_idea_detail,
)
from .services.ideas import (
    move_idea,
    reorder_column,
    quick_add_idea,
)
from django.utils import timezone
from ..models import Board, Column, Idea, IdeaProject


# -----------------------------------------------------------------------------
# Helpers (API-only)
# -----------------------------------------------------------------------------
def _ensure_auth(request):
    """Return a Django response (error) or None when authenticated."""
    return require_auth(request)


def _payload_or_400(request):
    payload = parse_payload(request)
    if not isinstance(payload, dict):
        return None, json_nostore({"error": "Invalid request body"}, status=400)
    return payload, None


def _get_board(board_id: int) -> Board:
    return get_object_or_404(Board, id=board_id)

def _get_board_owned(request, board_id: int) -> Board:
    return get_object_or_404(Board, id=board_id, owner=request.user)


def _get_idea_in_board(board: Board, idea_id: int) -> Idea:
    return get_object_or_404(
        Idea.objects.select_related("column").prefetch_related("tags"),
        id=idea_id,
        column__board=board,
    )



def _normalize_tags_value(tags_val):
    """Accept str 'a,b' or list; return list[str]."""
    if isinstance(tags_val, str):
        return [t.strip() for t in tags_val.split(",") if t.strip()]
    if isinstance(tags_val, list):
        return [str(t).strip() for t in tags_val if str(t).strip()]
    return []


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------
@require_GET
def board_idea_detail_api(request, board_id, idea_id):
    err = _ensure_auth(request)
    if err:
        return err

    board = _get_board_owned(request, board_id)

    idea = _get_idea_in_board(board, idea_id)

    return json_nostore({"board": serialize_board(board), "idea": serialize_idea_detail(idea)})


@require_POST
def board_idea_update_api(request, board_id, idea_id):
    """
    Mise à jour des champs d'une idée (édition).
    On garde la logique ici pour l'instant car elle touche plusieurs champs optionnels
    (tags / impact / next_action / body_md), mais la sérialisation est déportée.
    """
    err = _ensure_auth(request)
    if err:
        return err

    board = _get_board_owned(request, board_id)

    idea = _get_idea_in_board(board, idea_id)

    payload, bad = _payload_or_400(request)
    if bad:
        return bad

    updated_fields = []

    # title
    if "title" in payload:
        title = (payload.get("title") or "").strip()
        if not title:
            return json_nostore({"error": "Title is required"}, status=400)
        idea.title = title
        updated_fields.append("title")

    # body_md
    if "body_md" in payload:
        idea.body_md = payload.get("body_md") or ""
        updated_fields.append("body_md")

    # next_action (optional field)
    if "next_action" in payload and hasattr(idea, "next_action"):
        idea.next_action = payload.get("next_action") or ""
        updated_fields.append("next_action")

    # impact (optional field)
    if "impact" in payload and hasattr(idea, "impact"):
        impact_raw = payload.get("impact")
        if impact_raw in (None, ""):
            idea.impact = None
            updated_fields.append("impact")
        else:
            impact_int = get_int(payload, "impact", default="__invalid__")
            if impact_int == "__invalid__":
                return json_nostore({"error": "Impact must be an integer"}, status=400)
            idea.impact = impact_int
            updated_fields.append("impact")

    # column switch (optional)
    if "column_id" in payload:
        col_id = get_int(payload, "column_id")
        if col_id is None:
            return json_nostore({"error": "column_id must be an integer"}, status=400)

        new_col = get_object_or_404(Column, id=col_id, board=board)
        if idea.column_id != new_col.id:
            idea.column = new_col
            updated_fields.append("column")

    # Save core fields
    if updated_fields:
        idea.save(update_fields=updated_fields)
    else:
        idea.save()

    # Tags (optional)
    if "tags" in payload and hasattr(idea, "tags"):
        tags_list = _normalize_tags_value(payload.get("tags"))
        try:
            from ..models import Tag  # local import to avoid circular imports

            tag_objs = []
            for name in tags_list:
                tag, _ = Tag.objects.get_or_create(name=name)
                tag_objs.append(tag)
            idea.tags.set(tag_objs)
        except Exception:
            # keep API tolerant: tags failures shouldn't block updates
            pass

        # refresh to return current tags/column
        try:
            idea = _get_idea_in_board(board, idea.id)
        except Exception:
            pass

    return json_nostore({"idea": serialize_idea_detail(idea)})


@require_POST
def board_idea_convert_api(request, board_id, idea_id):
    """
    Convert an Idea into a Project.
    - Creates IdeaProject if not exists
    - Sets converted_at timestamp
    - Moves idea to the validated column (kind="validated")
    """
    err = _ensure_auth(request)
    if err:
        return err

    board = _get_board_owned(request, board_id)

    idea = _get_idea_in_board(board, idea_id)

    # Already converted
    if idea.converted_at:
        return json_nostore({"error": "Idea already converted"}, status=400)

    # Find validated column
    validated_col = (
        Column.objects
        .filter(board=board, kind="validated")
        .order_by("order", "id")
        .first()
    )

    if not validated_col:
        return json_nostore(
            {"error": "No validated column found on this board"},
            status=400,
        )

    # Create project extension
    project = IdeaProject.objects.create(idea=idea)

    # Update idea
    idea.converted_at = timezone.now()
    idea.column = validated_col
    idea.save(update_fields=["converted_at", "column"])

    debug_log(
        "[CONVERT] idea_id=%s -> project_id=%s column_id=%s",
        idea.id,
        project.id,
        validated_col.id,
    )

    # Reload idea with relations
    idea = _get_idea_in_board(board, idea.id)

    return json_nostore(
        {
            "ok": True,
            "idea": serialize_idea_detail(idea),
            "project": {
                "id": project.id,
                "created_at": project.created_at,
            },
        },
        status=201,
    )


@require_POST
def board_idea_move_api(request, board_id, idea_id):
    """
    Move/reorder via DnD.
    Le service gère la persistance de la position.
    """
    err = _ensure_auth(request)
    if err:
        return err

    board = _get_board_owned(request, board_id)

    idea = _get_idea_in_board(board, idea_id)

    payload, bad = _payload_or_400(request)
    if bad:
        return bad

    debug_log("[MOVE] board_id=%s idea_id=%s payload=%s", board_id, idea_id, payload)

    # Accept multiple client keys (legacy compatible)
    to_column_id = payload.get("to_column_id")
    column_id = payload.get("column_id") or payload.get("column")
    column_id = to_column_id or column_id

    if not column_id:
        return json_nostore({"error": "to_column_id/column_id is required"}, status=400)

    try:
        to_column_id = int(column_id)
    except Exception:
        return json_nostore({"error": "to_column_id/column_id must be an integer"}, status=400)

    # target_index may be missing; accept synonyms
    target_index = payload.get("target_index", payload.get("position", payload.get("order")))
    try:
        target_index = int(target_index) if target_index is not None else None
    except Exception:
        target_index = None

    idea = move_idea(
        board_id=int(board_id),
        idea_id=int(idea_id),
        to_column_id=int(to_column_id),
        target_index=target_index,
    )

    return json_nostore(
        {
            "ok": True,
            "idea": {
                "id": idea.id,
                "column_id": idea.column_id,
                **({"position": idea.position} if hasattr(idea, "position") else {}),
            },
        }
    )


@require_POST
def board_column_reorder_api(request, board_id, column_id):
    """
    Reorder strict d'une colonne (drag intra-colonne).
    """
    err = _ensure_auth(request)
    if err:
        return err

    board = _get_board_owned(request, int(board_id))
    column = get_object_or_404(Column, id=int(column_id), board=board)

    payload, bad = _payload_or_400(request)
    if bad:
        return bad

    ordered_ids = (
            payload.get("ordered_ids")
            or payload.get("orderedIds")
            or payload.get("ids")
            or payload.get("order")  # compat tests
    )
    if isinstance(ordered_ids, str):
        try:
            import json as _json
            ordered_ids = _json.loads(ordered_ids)
        except Exception:
            pass

    if not isinstance(ordered_ids, list) or len(ordered_ids) == 0:
        return json_nostore({"error": "ordered_ids must be a non-empty list"}, status=400)

    try:
        ordered_ids = [int(i) for i in ordered_ids]
    except Exception:
        return json_nostore({"error": "ordered_ids must be integers"}, status=400)

    # pas de doublons
    if len(set(ordered_ids)) != len(ordered_ids):
        return json_nostore({"error": "ordered_ids must not contain duplicates"}, status=400)

    # ids actuellement dans la colonne (ordre actuel)
    current_ids = list(
        Idea.objects.filter(column=column)
        .order_by("position", "id")
        .values_list("id", flat=True)
    )

    # ordered_ids doit être un sous-ensemble de la colonne
    current_set = set(current_ids)
    if any(i not in current_set for i in ordered_ids):
        return json_nostore({"error": "Some ideas do not belong to this column"}, status=400)

    # compléter automatiquement avec les ids manquants (robuste pour DnD/tests)
    missing = [i for i in current_ids if i not in ordered_ids]
    final_order = ordered_ids + missing

    debug_log("[REORDER] board_id=%s column_id=%s ordered_ids=%s final=%s", board_id, column_id, ordered_ids,
              final_order)

    try:
        reorder_column(board_id=int(board_id), column_id=int(column_id), ordered_ids=final_order)
    except ValueError:
        return json_nostore({"error": "Some ideas do not belong to this column"}, status=400)

    return json_nostore({"ok": True, "ordered_ids": final_order})


@require_POST
def board_idea_quick_add_api(request, board_id):
    """
    Quick add: parse du texte (#tags @colonne !impact) + création.
    La création en base (position fin de colonne) est déportée dans le service.
    """
    err = _ensure_auth(request)
    if err:
        return err

    board = _get_board_owned(request, board_id)

    payload, bad = _payload_or_400(request)
    if bad:
        return bad

    raw_text = (payload.get("text") or payload.get("title") or "").strip()
    column_id = payload.get("column_id")

    if not raw_text:
        return json_nostore({"error": "Text or title is required"}, status=400)

    # Simple inline parsing: #tag @column !impact
    words = raw_text.split()
    tag_names = []
    column_hint = None
    impact_value = None
    remaining = []

    for w in words:
        if w.startswith("#") and len(w) > 1:
            name = w[1:].strip().strip(",;")
            if name:
                tag_names.append(name)
            continue

        if w.startswith("@") and len(w) > 1:
            name = w[1:].strip().strip(",;")
            if name:
                column_hint = name
            continue

        if w.startswith("!") and len(w) > 1:
            n = w[1:].strip().strip(",;")
            try:
                impact_value = int(n)
                continue
            except Exception:
                pass

        remaining.append(w)

    title = " ".join(remaining).strip() or raw_text

    # Resolve destination column_id
    resolved_column_id = None

    if column_id is not None:
        try:
            resolved_column_id = int(column_id)
        except Exception:
            return json_nostore({"error": "column_id must be an integer"}, status=400)
    elif column_hint:
        col = Column.objects.filter(board=board, name__iexact=column_hint).order_by("order", "id").first()
        if col:
            resolved_column_id = col.id

    # Create idea (service sets position at end when supported)
    try:
        idea = quick_add_idea(board_id=int(board_id), title=title, column_id=resolved_column_id)
    except ValueError as e:
        return json_nostore({"error": str(e)}, status=400)

    # impact (optional)
    if impact_value is not None and hasattr(idea, "impact"):
        try:
            idea.impact = impact_value
            idea.save(update_fields=["impact"])
        except Exception:
            pass

    # tags (optional)
    if tag_names and hasattr(idea, "tags"):
        try:
            from ..models import Tag

            for name in tag_names:
                tag, _ = Tag.objects.get_or_create(name=name)
                idea.tags.add(tag)
        except Exception:
            pass

        # refresh for tags
        try:
            idea = _get_idea_in_board(board, idea.id)
        except Exception:
            pass

    return json_nostore({"idea": serialize_idea_card(idea)}, status=201)
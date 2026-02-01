import json
import re
import logging
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_protect
from django.shortcuts import get_object_or_404, redirect, render
from django.db.models import Max, Q, Prefetch
from django.http import Http404
from .models import Board, Tag, Idea, IdeaTemplate
from .forms import IdeaForm, IdeaCreateForm, IdeaTemplateFromIdeaForm
from .utils import render_markdown


logger = logging.getLogger(__name__)

def _remember_board(request, board_id: int) -> None:
    """Mémorise le dernier board visité pour un 'board courant' intelligent."""
    request.session["current_board_id"] = int(board_id)

def home_view(request):
    """Page d'accueil: présente StudioBoard et propose l'accès aux boards."""
    # Si l'utilisateur passe ?board=<id>, on redirige directement (comportement explicite)
    board_id = (request.GET.get("board") or "").strip()
    if board_id.isdigit():
        return redirect("board:kanban", board_id=int(board_id))

    boards = list(Board.objects.order_by("id"))
    first_board = boards[0] if boards else None

    last_ideas = (
        Idea.objects
        .select_related("column", "column__board")
        .prefetch_related("tags")
        .order_by("-created_at")[:3]
    )

    return render(
        request,
        "board/home.html",
        {
            "boards": boards,
            "first_board": first_board,
            "last_ideas": last_ideas,
        },
    )

def _bottom_position_for_column(column_id: int) -> int:
    max_pos = (
        Idea.objects.filter(column_id=column_id)
        .aggregate(Max("position"))
        .get("position__max")
    )
    return 0 if max_pos is None else max_pos + 1


def _uniq_ci(names):
    uniq = []
    for name in names:
        name = (name or "").strip()
        if not name:
            continue
        if name.casefold() not in [u.casefold() for u in uniq]:
            uniq.append(name)
    return uniq


def _parse_tags_text(tags_text: str):
    # tags_text attendu: "tag1, tag2, #tag3"
    parts = [t.strip().lstrip("#") for t in (tags_text or "").split(",") if t.strip()]
    return _uniq_ci(parts)


def _set_tags_for_idea(idea: Idea, tag_names):
    tag_names = _uniq_ci(tag_names)
    tags = []
    for name in tag_names:
        tag, _ = Tag.objects.get_or_create(name=name)
        tags.append(tag)
    idea.tags.set(tags)

def kanban_view(request, board_id: int):
    board = get_object_or_404(Board, id=board_id)
    _remember_board(request, board_id)

    q = (request.GET.get("q") or "").strip()
    tag = (request.GET.get("tag") or "").strip()
    col = (request.GET.get("col") or "").strip()

    idea_qs = (
        Idea.objects.filter(column__board=board)
        .prefetch_related("tags")
        .order_by("position", "id")
    )

    if q:
        idea_qs = idea_qs.filter(Q(title__icontains=q) | Q(body_md__icontains=q))

    if tag:
        # tag exact, insensible à la casse
        idea_qs = idea_qs.filter(tags__name__iexact=tag)

    if col.isdigit():
        idea_qs = idea_qs.filter(column_id=int(col))

    idea_qs = idea_qs.distinct()

    # Prefetch filtré : chaque colonne n’aura que ses idées filtrées
    columns = (
        board.columns
        .order_by("order", "id")
        .prefetch_related(Prefetch("ideas", queryset=idea_qs))
        .all()
    )

    context = {
        "board": board,
        "columns": columns,
        "q": q,
        "tag": tag,
        "col": col,
    }
    return render(request, "board/kanban.html", context)

def idea_create_view(request, board_id: int):
    board = get_object_or_404(Board, id=board_id)
    _remember_board(request, board_id)

    # GET: afficher le formulaire vide
    if request.method != "POST":
        form = IdeaCreateForm(board=board)
        return render(request, "board/idea_form.html", {"board": board, "form": form})

    # POST: traiter la soumission
    form = IdeaCreateForm(request.POST, board=board)

    if not form.is_valid():
        logger.warning(
            "IdeaCreateForm invalid | board_id=%s | errors=%s | post_keys=%s",
            board_id,
            dict(form.errors),
            list(request.POST.keys()),
        )
        return render(request, "board/idea_form.html", {"board": board, "form": form})

    # Form valide: on peut créer l'idée
    idea = form.save(commit=False)

    # Sécurité: si aucune colonne n'est fournie (cas rare), fallback sur la 1ère colonne du board
    if not idea.column_id:
        first_col = board.columns.order_by("order", "id").first()
        if first_col is None:
            return redirect("board:kanban", board_id=board.id)
        idea.column = first_col

    # Position: en bas de la colonne
    idea.position = _bottom_position_for_column(idea.column_id)

    # Template (optionnel): ne remplit que si body_md est vide
    selected_template = form.cleaned_data.get("template_id")
    if selected_template and not (idea.body_md or "").strip():
        idea.body_md = selected_template.body_md

    # Statut par défaut à la création
    if not getattr(idea, "status", None):
        idea.status = "active"  # adapte si ta valeur diffère

    idea.save()
    form.save_m2m()

    # Tags (si ton form expose tags_text)
    tags_text = form.cleaned_data.get("tags_text", "")
    _set_tags_for_idea(idea, _parse_tags_text(tags_text))

    return redirect("board:idea_detail", board_id=board.id, idea_id=idea.id)


def idea_detail_view(request, board_id: int, idea_id: int):
    board = get_object_or_404(Board, id=board_id)
    _remember_board(request, board_id)

    # On va chercher l'idée en s'assurant qu'elle appartient bien à ce board
    idea = (
        Idea.objects.select_related("column", "column__board")
        .prefetch_related("tags")
        .filter(id=idea_id, column__board=board)
        .first()
    )
    if idea is None:
        raise Http404("Idée introuvable pour ce board.")

    html_body = render_markdown(idea.body_md)

    return render(
        request,
        "board/idea_detail.html",
        {"board": board, "idea": idea, "idea_html": html_body},
    )


def idea_edit_view(request, board_id: int, idea_id: int):
    board = get_object_or_404(Board, id=board_id)
    _remember_board(request, board_id)

    idea = (
        Idea.objects.select_related("column", "column__board")
        .prefetch_related("tags")
        .filter(id=idea_id, column__board=board)
        .first()
    )
    if idea is None:
        raise Http404("Idée introuvable pour ce board.")

    if request.method == "POST":
        form = IdeaForm(request.POST, instance=idea, board=board)
        if form.is_valid():
            # Détecter un changement de colonne AVANT save()
            old_column_id = idea.column_id

            idea = form.save(commit=False)

            if idea.column_id != old_column_id:
                idea.position = _bottom_position_for_column(idea.column_id)

            idea.save()
            form.save_m2m()  # (ne gère pas tags_text, mais garde une cohérence si tu ajoutes d'autres M2M plus tard)

            # Tags: créer si besoin + associer
            tags_text = form.cleaned_data.get("tags_text", "")
            _set_tags_for_idea(idea, _parse_tags_text(tags_text))
            return redirect("board:idea_detail", board_id=board.id, idea_id=idea.id)
    else:
        form = IdeaForm(instance=idea, board=board)

    templates = IdeaTemplate.objects.filter(is_active=True).order_by("name")
    return render(request, "board/idea_edit.html", {"board": board, "idea": idea, "form": form, "templates": templates})


def idea_save_template_view(request, board_id: int, idea_id: int):
    board = get_object_or_404(Board, id=board_id)
    _remember_board(request, board_id)
    idea = get_object_or_404(Idea, id=idea_id, column__board=board)

    if request.method == "POST":
        form = IdeaTemplateFromIdeaForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data["name"].strip()
            is_active = form.cleaned_data["is_active"]

            if not (idea.body_md or "").strip():
                form.add_error(None, "Cette idée n’a pas de contenu Markdown à sauvegarder.")
                return render(request, "board/idea_save_template.html", {"board": board, "idea": idea, "form": form})

            IdeaTemplate.objects.create(
                name=name,
                body_md=idea.body_md or "",
                is_active=is_active,
            )

            return redirect("board:idea_detail", board_id=board.id, idea_id=idea.id)
    else:
        # Nom proposé par défaut (tu peux ajuster)
        form = IdeaTemplateFromIdeaForm(initial={"name": idea.title, "is_active": True})

    return render(
        request,
        "board/idea_save_template.html",
        {"board": board, "idea": idea, "form": form},
    )
@require_POST
def kanban_reorder_view(request, board_id: int):
    """
    Reçoit un JSON de la forme:
    {
      "columns": [
        {"id": 10, "idea_ids": [5, 2, 9]},
        {"id": 11, "idea_ids": []},
        ...
      ]
    }
    Met à jour column_id et position pour toutes les idées concernées.
    """
    board = get_object_or_404(Board, id=board_id)
    _remember_board(request, board_id)

    try:
        payload = json.loads(request.body.decode("utf-8"))
        columns_payload = payload.get("columns", [])
    except Exception:
        return JsonResponse({"ok": False, "error": "invalid_json"}, status=400)

    # Récup des colonnes du board (sécurité)
    board_column_ids = set(board.columns.values_list("id", flat=True))

    # On construit la liste des updates attendus: (idea_id -> (column_id, position))
    updates = {}
    seen_idea_ids = set()

    for col in columns_payload:
        col_id = col.get("id")
        idea_ids = col.get("idea_ids", [])

        if col_id not in board_column_ids:
            return JsonResponse({"ok": False, "error": "invalid_column"}, status=400)

        # Normalisation: seulement des int, positions 0..n-1
        for pos, idea_id in enumerate(idea_ids):
            if not isinstance(idea_id, int):
                return JsonResponse({"ok": False, "error": "invalid_idea_id_type"}, status=400)
            updates[idea_id] = (col_id, pos)
            seen_idea_ids.add(idea_id)

    # Sécurité: vérifier que toutes les idées reçues appartiennent bien au board
    valid_idea_ids = set(
        Idea.objects.filter(id__in=seen_idea_ids, column__board=board).values_list("id", flat=True)
    )
    if valid_idea_ids != seen_idea_ids:
        return JsonResponse({"ok": False, "error": "idea_not_in_board"}, status=400)

    # Appliquer les updates en transaction
    with transaction.atomic():
        ideas = Idea.objects.select_for_update().filter(id__in=seen_idea_ids)
        for idea in ideas:
            col_id, pos = updates[idea.id]
            if idea.column_id != col_id or idea.position != pos:
                idea.column_id = col_id
                idea.position = pos

        Idea.objects.bulk_update(ideas, ["column_id", "position"])

    return JsonResponse({"ok": True})

@require_POST
def quick_add_view(request, board_id: int):
    board = get_object_or_404(Board, id=board_id)
    _remember_board(request, board_id)

    raw = (request.POST.get("title") or "").strip()
    if not raw:
        return redirect("board:kanban", board_id=board.id)

    text = raw

    # --- Colonne: @Name ou @"Name with spaces" ---
    col_name = None
    m = re.search(r'@"([^"]+)"', text)
    if m:
        col_name = m.group(1).strip()
        text = (text[: m.start()] + text[m.end() :]).strip()
    else:
        m = re.search(r"@([^\s]+)", text)
        if m:
            col_name = m.group(1).strip()
            text = (text[: m.start()] + text[m.end() :]).strip()

    # --- Impact: !N ou i:N (0..5) ---
    impact = None
    m = re.search(r"(?:!|i:)\s*([0-5])\b", text)
    if m:
        impact = int(m.group(1))
        text = (text[: m.start()] + text[m.end() :]).strip()

    # --- Tags: #tag ---
    tag_names = re.findall(r"#([\w-]+)", text)
    if tag_names:
        # Retirer les tags du titre
        text = re.sub(r"\s*#[\w-]+", "", text).strip()

    title = text.strip().strip('"')
    if not title:
        # si l'utilisateur n'a mis que des meta (tags/impact/col), on garde le raw
        title = raw

    # Colonne cible
    target_col = None
    if col_name:
        cols = list(board.columns.all())
        col_name_l = col_name.casefold()

        # match exact
        for c in cols:
            if c.name.casefold() == col_name_l:
                target_col = c
                break

        # match tolérant (startswith)
        if target_col is None:
            for c in cols:
                if c.name.casefold().startswith(col_name_l):
                    target_col = c
                    break

    # fallback: 1ère colonne du board
    if target_col is None:
        target_col = board.columns.order_by("order", "id").first()

    if target_col is None:
        return redirect("board:kanban", board_id=board.id)

    # Position: en bas de la colonne
    position = _bottom_position_for_column(target_col.id)

    idea_kwargs = {
        "column": target_col,
        "title": title,
        "position": position,
    }
    if impact is not None:
        idea_kwargs["impact"] = impact

    # ⚠️ Pas de IdeaStatus ici -> on laisse le default du modèle
    idea = Idea.objects.create(**idea_kwargs)

    # Associer tags (création si besoin)
    if tag_names:
        _set_tags_for_idea(idea, tag_names)

    return redirect("board:kanban", board_id=board.id)


@require_GET
def template_preview_view(request, board_id: int):
    """
    Retourne le body_md d'un template actif pour prévisualisation côté front.
    Appel: /b/<board_id>/templates/preview/?id=<template_id>
    """
    # On garde board_id pour rester dans le namespace du board
    get_object_or_404(Board, id=board_id)
    _remember_board(request, board_id)

    template_id = (request.GET.get("id") or "").strip()
    if not template_id.isdigit():
        return JsonResponse({"ok": False, "error": "invalid_template_id"}, status=400)

    tpl = get_object_or_404(IdeaTemplate, id=int(template_id), is_active=True)
    return JsonResponse(
        {"ok": True, "template": {"id": tpl.id, "name": tpl.name, "body_md": tpl.body_md}}
    )


@require_POST
def idea_apply_template_view(request, board_id: int, idea_id: int):
    board = get_object_or_404(Board, id=board_id)
    _remember_board(request, board_id)
    idea = get_object_or_404(Idea, id=idea_id, column__board=board)

    template_id = request.POST.get("template_id")
    if not template_id:
        return redirect("board:idea_edit", board_id=board.id, idea_id=idea.id)

    template = get_object_or_404(IdeaTemplate, id=template_id, is_active=True)

    # Remplace le contenu markdown par celui du template
    idea.body_md = template.body_md
    idea.save(update_fields=["body_md"])

    return redirect("board:idea_edit", board_id=board.id, idea_id=idea.id)

def template_list_view(request, board_id: int):
    board = get_object_or_404(Board, id=board_id)
    _remember_board(request, board_id)
    templates = IdeaTemplate.objects.order_by("-is_active", "name")
    return render(request, "board/template_list.html", {"board": board, "templates": templates})

def template_toggle_view(request, board_id: int, template_id: int):
    get_object_or_404(Board, id=board_id)  # juste pour rester cohérent / sécurité
    _remember_board(request, board_id)
    template = get_object_or_404(IdeaTemplate, id=template_id)
    template.is_active = not template.is_active
    template.save(update_fields=["is_active"])
    return redirect("board:template_list", board_id=board_id)


def template_edit_view(request, board_id: int, template_id: int):
    board = get_object_or_404(Board, id=board_id)
    _remember_board(request, board_id)
    template = get_object_or_404(IdeaTemplate, id=template_id)

    if request.method == "POST":
        template.name = request.POST.get("name", "").strip()
        template.body_md = request.POST.get("body_md", "")
        template.is_active = bool(request.POST.get("is_active"))
        template.save()
        return redirect("board:template_list", board_id=board_id)

    return render(request, "board/template_edit.html", {"board": board, "template": template})

@csrf_protect
@require_POST
def markdown_preview_view(request, board_id: int):
    """
    Rendu Markdown -> HTML pour prévisualisation live côté front.
    """
    get_object_or_404(Board, id=board_id)
    _remember_board(request, board_id)

    body_md = request.POST.get("body_md", "") or ""
    html = render_markdown(body_md) if body_md.strip() else ""

    return JsonResponse({"ok": True, "html": html})
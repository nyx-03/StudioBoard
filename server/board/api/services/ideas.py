from django.db import transaction
from django.db.models import F, Max
from django.shortcuts import get_object_or_404

from ...models import Board, Column, Idea
from ..debug import debug_log


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _normalize_position(column, ids=None):
    """
    Recalcule des positions compactes (0..n-1) dans une colonne.
    Si `ids` est fourni, on l’utilise comme source d’ordre (liste d’IDs).
    """
    if ids is None:
        ids = list(
            Idea.objects.filter(column=column)
            .order_by("position", "id")
            .values_list("id", flat=True)
        )
    for idx, iid in enumerate(ids):
        Idea.objects.filter(id=iid, column=column).update(position=idx)


# ---------------------------------------------------------------------------
# Services
# ---------------------------------------------------------------------------
def move_idea(*, board_id, idea_id, to_column_id, target_index=None):
    """
    Déplace une idée :
    - intra-colonne (reorder)
    - inter-colonne (move)
    Persiste toujours la position.

    Remarques :
    - `target_index` est l’index "d’insertion" côté UI (entre deux cartes).
    - On reconstruit la liste d’IDs source/destination pour éviter les cas limites
      (positions NULL, colonne vide, décalages incohérents).
    """
    board = get_object_or_404(Board, id=board_id)
    idea = get_object_or_404(
        Idea.objects.select_related("column"),
        id=idea_id,
        column__board=board,
    )
    new_column = get_object_or_404(Column, id=to_column_id, board=board)

    # Pas de champ position => on ne gère que le changement de colonne
    if not hasattr(Idea, "position"):
        if idea.column_id != new_column.id:
            idea.column = new_column
            idea.save(update_fields=["column"])
        return idea

    # Normalise target_index
    try:
        target_index = int(target_index) if target_index is not None else None
    except Exception:
        target_index = None

    with transaction.atomic():
        old_column = idea.column

        # Source: liste ordonnée (exclure l’idée déplacée)
        src_ids = list(
            Idea.objects.filter(column=old_column)
            .exclude(id=idea.id)
            .order_by("position", "id")
            .values_list("id", flat=True)
        )

        # Destination: liste ordonnée (exclure l’idée déplacée)
        dest_ids = list(
            Idea.objects.filter(column=new_column)
            .exclude(id=idea.id)
            .order_by("position", "id")
            .values_list("id", flat=True)
        )

        # Index courant (utile en intra-colonne)
        current_ids = []
        if old_column.id == new_column.id:
            current_ids = list(
                Idea.objects.filter(column=old_column)
                .order_by("position", "id")
                .values_list("id", flat=True)
            )
            try:
                current_index = current_ids.index(idea.id)
            except ValueError:
                # Si incohérence, on considère que l’idée est en fin
                current_index = len(current_ids)
        else:
            current_index = None

        # Borne de l'index d’insertion
        if target_index is None:
            insert_at = len(dest_ids)
        else:
            insert_at = max(0, min(target_index, len(dest_ids)))

        # Intra-colonne : si on se déplace vers le bas, l’index d’insertion
        # reçu inclut souvent la carte en cours; on ajuste comme dans la view initiale.
        if old_column.id == new_column.id and current_index is not None:
            # current_ids inclut l’idée; insert_at est relatif à dest_ids (sans l’idée)
            # On ajuste en se basant sur l’index cible "UI" par rapport à current_ids.
            # Si la cible est après la position actuelle, on décrémente.
            if target_index is not None and target_index > current_index:
                insert_at = max(0, insert_at - 1)

            # Reconstruit l’ordre final
            final_ids = list(src_ids)
            insert_at = max(0, min(insert_at, len(final_ids)))
            final_ids.insert(insert_at, idea.id)

            # Met à jour uniquement la position
            idea.position = insert_at
            idea.save(update_fields=["position"])

            # Normalise toute la colonne avec l’ordre final
            _normalize_position(old_column, ids=final_ids)

            debug_log(
                "[SERVICE move_idea intra] idea=%s column=%s from=%s to=%s final_index=%s size=%s",
                idea.id,
                old_column.id,
                current_index,
                insert_at,
                idea.position,
                len(final_ids),
            )
            return idea

        # Inter-colonne : on insère dans la destination, et on normalise source+dest
        dest_ids.insert(insert_at, idea.id)

        # Change la colonne + position (provisoirement) avant normalisation
        idea.column = new_column
        idea.position = insert_at
        idea.save(update_fields=["column", "position"])

        # Normalise la source et la destination (ordre déterministe)
        _normalize_position(old_column, ids=src_ids)
        _normalize_position(new_column, ids=dest_ids)

        debug_log(
            "[SERVICE move_idea inter] idea=%s from_column=%s to_column=%s insert_at=%s src_size=%s dest_size=%s",
            idea.id,
            old_column.id,
            new_column.id,
            insert_at,
            len(src_ids),
            len(dest_ids),
        )

    return idea


def reorder_column(*, board_id, column_id, ordered_ids):
    """
    Reorder strict d'une colonne (drag intra-colonne).
    """
    board = get_object_or_404(Board, id=board_id)
    column = get_object_or_404(Column, id=column_id, board=board)

    if not hasattr(Idea, "position"):
        return

    ids = [int(i) for i in ordered_ids]

    ideas = list(Idea.objects.filter(column=column, id__in=ids))
    if len(ideas) != len(ids):
        raise ValueError("Invalid idea list for reorder")

    with transaction.atomic():
        for index, iid in enumerate(ids):
            Idea.objects.filter(id=iid, column=column).update(position=index)

    debug_log(
        "[SERVICE reorder_column] column=%s ids=%s",
        column.id,
        ids,
    )


def quick_add_idea(*, board_id, title, column_id=None):
    """
    Création rapide d'idée, ajoutée en fin de colonne.
    """
    board = get_object_or_404(Board, id=board_id)

    if column_id:
        column = get_object_or_404(Column, id=column_id, board=board)
    else:
        column = Column.objects.filter(board=board).order_by("order", "id").first()
        if not column:
            raise ValueError("Board has no columns")

    if hasattr(Idea, "position"):
        max_pos = (
            Idea.objects.filter(column=column)
            .aggregate(max_pos=Max("position"))
            .get("max_pos")
        )
        pos = (max_pos + 1) if max_pos is not None else 0
        idea = Idea.objects.create(title=title, column=column, position=pos)
    else:
        idea = Idea.objects.create(title=title, column=column)

    debug_log(
        "[SERVICE quick_add] idea=%s column=%s",
        idea.id,
        column.id,
    )

    return idea
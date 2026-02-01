from .models import Board

def studio_context(request):
    """
    Expose un 'board courant' basé sur la session.
    Fallback: premier board si aucun board courant.
    """
    current_board = None
    current_board_id = request.session.get("current_board_id")

    if isinstance(current_board_id, int):
        current_board = Board.objects.filter(id=current_board_id).first()

    first_board = Board.objects.order_by("id").first()
    if current_board is None:
        current_board = first_board

    return {
        "current_board": current_board,
        "first_board": current_board,  # rétro-compat si tes templates utilisent first_board
        "all_boards": Board.objects.order_by("id"),
    }
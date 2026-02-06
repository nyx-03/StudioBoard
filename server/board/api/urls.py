# API routes consumed by Next.js (API-first)
from django.urls import path

from .views_auth import (
    auth_me_api,
    auth_login_api,
    auth_logout_api,
    auth_csrf_api,
)
from .views_boards import (
    boards_list_api,
    board_kanban_api,
)
from .views_ideas import (
    board_idea_detail_api,
    board_idea_quick_add_api,
    board_idea_update_api,
    board_idea_move_api,
    board_column_reorder_api,
)

urlpatterns = [
    # Boards
    path("boards", boards_list_api, name="api_boards_list"),
    path("boards/<int:board_id>/kanban", board_kanban_api, name="api_board_kanban"),

    # Ideas
    path(
        "boards/<int:board_id>/ideas/quick-add",
        board_idea_quick_add_api,
        name="api_board_idea_quick_add",
    ),
    path(
        "boards/<int:board_id>/ideas/<int:idea_id>",
        board_idea_detail_api,
        name="api_board_idea_detail",
    ),
    path(
        "boards/<int:board_id>/ideas/<int:idea_id>/update",
        board_idea_update_api,
        name="api_board_idea_update",
    ),
    path(
        "boards/<int:board_id>/ideas/<int:idea_id>/move",
        board_idea_move_api,
        name="api_board_idea_move",
    ),

    # Columns
    path(
        "boards/<int:board_id>/columns/<int:column_id>/reorder",
        board_column_reorder_api,
        name="api_board_column_reorder",
    ),

    # Auth
    path("auth/me", auth_me_api, name="api_auth_me"),
    path("auth/login", auth_login_api, name="api_auth_login"),
    path("auth/logout", auth_logout_api, name="api_auth_logout"),
    path("auth/csrf", auth_csrf_api, name="api_auth_csrf"),
]
from django.urls import path
from .views import (
    kanban_view,
    idea_create_view,
    idea_detail_view,
    idea_edit_view,
    kanban_reorder_view,
    quick_add_view,
    idea_apply_template_view,
    template_preview_view,
    idea_save_template_view,
    template_list_view,
    template_edit_view,
    template_toggle_view,
    markdown_preview_view,
)

app_name = "board"

urlpatterns = [
    path("b/<int:board_id>/", kanban_view, name="kanban"),
    path("b/<int:board_id>/new/", idea_create_view, name="idea_new"),
    path("b/<int:board_id>/i/<int:idea_id>/", idea_detail_view, name="idea_detail"),
    path("b/<int:board_id>/i/<int:idea_id>/edit/", idea_edit_view, name="idea_edit"),
    path("b/<int:board_id>/reorder/", kanban_reorder_view, name="kanban_reorder"),
    path("b/<int:board_id>/quick-add/", quick_add_view, name="quick_add"),
    path(
        "b/<int:board_id>/i/<int:idea_id>/apply-template/",
        idea_apply_template_view,
        name="idea_apply_template",
    ),
    path(
        "b/<int:board_id>/templates/preview/",
        template_preview_view,
        name="template_preview",
    ),
    path(
        "b/<int:board_id>/i/<int:idea_id>/save-template/",
        idea_save_template_view,
        name="idea_save_template",
    ),
    path("b/<int:board_id>/templates/", template_list_view, name="template_list"),
    path("b/<int:board_id>/templates/<int:template_id>/edit/", template_edit_view, name="template_edit"),
    path("b/<int:board_id>/templates/<int:template_id>/toggle/", template_toggle_view, name="template_toggle"),
    path("b/<int:board_id>/md/preview/", markdown_preview_view, name="md_preview"),
]
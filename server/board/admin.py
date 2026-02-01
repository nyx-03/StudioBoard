from django.contrib import admin
from .models import Board, Column, Idea, Tag, IdeaTemplate


@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at", "updated_at")
    search_fields = ("name",)


@admin.register(Column)
class ColumnAdmin(admin.ModelAdmin):
    list_display = ("name", "board", "order", "created_at")
    list_filter = ("board",)
    ordering = ("board", "order")


@admin.register(Idea)
class IdeaAdmin(admin.ModelAdmin):
    list_display = ("title", "column", "position", "status", "impact", "updated_at")
    list_filter = ("status", "column__board")
    search_fields = ("title", "body_md", "next_action")
    filter_horizontal = ("tags",)
    ordering = ("column", "position")


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(IdeaTemplate)
class IdeaTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "description", "body_md")
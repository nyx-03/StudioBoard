from django.contrib import admin

from .models import Category, Item


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "color", "updated_at")
    search_fields = ("name",)


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ("title", "type", "status", "category", "updated_at")
    list_filter = ("type", "status", "category")
    search_fields = ("title", "content")
    actions = ("convert_to_project",)

    @admin.action(description="Convertir en projet")
    def convert_to_project(self, request, queryset):
        for item in queryset:
            item.convert_to_project()
            item.save(update_fields=["type", "status", "updated_at"])


admin.site.site_header = "StudioBoard"
admin.site.site_title = "StudioBoard Admin"
admin.site.index_title = "Administration StudioBoard"

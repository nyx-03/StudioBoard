from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),

    # API consommée par Next.js
    path("api/", include("board.api.urls")),
]
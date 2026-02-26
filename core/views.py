import json
import os
import platform
import re
import shutil
import socket
import subprocess
import zipfile
from datetime import datetime
from pathlib import Path, PurePosixPath
from urllib.parse import quote

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView

from .forms import CategoryForm, ItemForm
from .models import Category, Item


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "core/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["ideas"] = Item.objects.filter(type=Item.TYPE_IDEA).select_related("category")
        context["projects"] = Item.objects.filter(type=Item.TYPE_PROJECT).select_related("category")
        context["categories"] = Category.objects.all()
        return context


class KanbanView(LoginRequiredMixin, TemplateView):
    template_name = "core/kanban.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ideas = Item.objects.filter(type=Item.TYPE_IDEA).select_related("category")
        projects = Item.objects.filter(type=Item.TYPE_PROJECT).select_related("category")

        context["idea_columns"] = [
            {
                "key": key,
                "label": label,
                "items": ideas.filter(status=key),
            }
            for key, label in Item.IDEA_STATUSES
        ]
        context["project_columns"] = [
            {
                "key": key,
                "label": label,
                "items": projects.filter(status=key),
            }
            for key, label in Item.PROJECT_STATUSES
        ]
        return context


def _format_bytes(value):
    if value is None:
        return "N/A"
    units = ["o", "Ko", "Mo", "Go", "To"]
    size = float(value)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.1f} {unit}".replace(".0", "")
        size /= 1024
    return f"{size:.1f} To"


def _format_percent(value):
    if value is None:
        return "N/A"
    return f"{value:.1f} %"


def _format_duration(seconds):
    if seconds is None:
        return "N/A"
    seconds = int(seconds)
    days, rem = divmod(seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, _ = divmod(rem, 60)
    if days:
        return f"{days}j {hours}h {minutes}m"
    if hours:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


def _read_uptime_seconds():
    try:
        with open("/proc/uptime", "r", encoding="utf-8") as handle:
            return float(handle.read().split()[0])
    except (FileNotFoundError, ValueError, OSError):
        return None


def _read_cpu_temp():
    paths = [
        "/sys/class/thermal/thermal_zone0/temp",
        "/sys/class/thermal/thermal_zone1/temp",
    ]
    for path in paths:
        try:
            with open(path, "r", encoding="utf-8") as handle:
                raw = handle.read().strip()
            if raw:
                return float(raw) / 1000.0
        except (FileNotFoundError, ValueError, OSError):
            continue

    try:
        result = subprocess.run(
            ["vcgencmd", "measure_temp"],
            capture_output=True,
            text=True,
            check=True,
        )
        match = re.search(r"temp=([0-9.]+)", result.stdout)
        if match:
            return float(match.group(1))
    except (FileNotFoundError, subprocess.CalledProcessError, ValueError):
        return None

    return None


def _read_meminfo():
    try:
        with open("/proc/meminfo", "r", encoding="utf-8") as handle:
            lines = handle.readlines()
    except (FileNotFoundError, OSError):
        return None

    data = {}
    for line in lines:
        parts = line.split(":")
        if len(parts) != 2:
            continue
        key = parts[0].strip()
        value_parts = parts[1].strip().split()
        if not value_parts:
            continue
        try:
            data[key] = int(value_parts[0]) * 1024
        except ValueError:
            continue
    total = data.get("MemTotal")
    available = data.get("MemAvailable", data.get("MemFree"))
    if total is None:
        return None
    used = total - (available or 0)
    percent = (used / total * 100) if total else None
    return {
        "total": total,
        "available": available,
        "used": used,
        "percent": percent,
    }


class SystemInfoView(LoginRequiredMixin, TemplateView):
    template_name = "core/system_info.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        disk = shutil.disk_usage("/")
        mem = _read_meminfo()
        cpu_temp = _read_cpu_temp()
        uptime_seconds = _read_uptime_seconds()

        try:
            load_avg = os.getloadavg()
            load_avg = f"{load_avg[0]:.2f} / {load_avg[1]:.2f} / {load_avg[2]:.2f}"
        except (AttributeError, OSError):
            load_avg = "N/A"

        context["system"] = {
            "hostname": socket.gethostname(),
            "os": platform.platform(),
            "kernel": platform.release(),
            "python": platform.python_version(),
            "cpu_count": os.cpu_count() or "N/A",
            "load_avg": load_avg,
            "uptime": _format_duration(uptime_seconds),
            "temperature": f"{cpu_temp:.1f} °C" if cpu_temp is not None else "N/A",
            "memory_total": _format_bytes(mem["total"]) if mem else "N/A",
            "memory_used": _format_bytes(mem["used"]) if mem else "N/A",
            "memory_available": _format_bytes(mem["available"]) if mem else "N/A",
            "memory_percent": _format_percent(mem["percent"]) if mem else "N/A",
            "disk_total": _format_bytes(disk.total),
            "disk_used": _format_bytes(disk.used),
            "disk_free": _format_bytes(disk.free),
            "disk_percent": _format_percent(disk.used / disk.total * 100 if disk.total else None),
        }
        return context


def _safe_projects_root():
    root = Path(settings.PROJECTS_ROOT).expanduser()
    try:
        root = root.resolve()
    except FileNotFoundError:
        root = root.resolve(strict=False)
    return root


def _resolve_projects_path(root: Path, rel_path: str) -> Path:
    rel_path = (rel_path or "").strip().lstrip("/\\")
    candidate = (root / rel_path).resolve()
    if candidate != root and root not in candidate.parents:
        raise ValueError("Chemin invalide.")
    return candidate


def _sanitize_name(name: str):
    cleaned = (name or "").strip().replace("..", "")
    if not cleaned:
        return None
    if "/" in cleaned or "\\" in cleaned:
        return None
    return cleaned


def _normalize_upload_path(name: str) -> Path:
    raw = (name or "").replace("\\", "/")
    path = PurePosixPath(raw)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("Chemin invalide.")
    return Path(*path.parts)


def _safe_write_upload(target_root: Path, relative_path: Path, file_obj):
    if not relative_path.parts:
        return
    destination = (target_root / relative_path).resolve()
    if destination != target_root and target_root not in destination.parents:
        raise ValueError("Chemin invalide.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with open(destination, "wb") as handle:
        for chunk in file_obj.chunks():
            handle.write(chunk)


def _safe_extract_zip(zip_file: zipfile.ZipFile, target_dir: Path):
    for member in zip_file.infolist():
        member_name = member.filename
        if member_name.endswith("/"):
            continue
        destination = (target_dir / member_name).resolve()
        if destination != target_dir and target_dir not in destination.parents:
            raise ValueError("Chemin de zip invalide.")
        destination.parent.mkdir(parents=True, exist_ok=True)
        with zip_file.open(member) as source, open(destination, "wb") as target:
            shutil.copyfileobj(source, target)


class ProjectsView(LoginRequiredMixin, View):
    template_name = "core/projects.html"

    def get(self, request):
        return render(request, self.template_name, self._build_context(request))

    def post(self, request):
        root = _safe_projects_root()
        root.mkdir(parents=True, exist_ok=True)
        rel_path = request.POST.get("path", "")
        try:
            current_path = _resolve_projects_path(root, rel_path)
        except ValueError:
            messages.error(request, "Chemin invalide.")
            return redirect("projects")

        action = request.POST.get("action")
        if action == "create_folder":
            name = _sanitize_name(request.POST.get("new_folder"))
            if not name:
                messages.error(request, "Nom de dossier requis.")
            else:
                target = current_path / name
                if target.exists():
                    messages.error(request, "Ce dossier existe deja.")
                else:
                    target.mkdir(parents=True, exist_ok=True)
                    messages.success(request, "Dossier cree.")

        if action == "upload":
            upload = request.FILES.get("project_zip")
            project_name = _sanitize_name(request.POST.get("project_name"))
            if not upload:
                messages.error(request, "Fichier zip requis.")
            elif not upload.name.lower().endswith(".zip"):
                messages.error(request, "Seuls les fichiers .zip sont acceptes.")
            else:
                safe_name = project_name or Path(upload.name).stem
                safe_name = _sanitize_name(safe_name)
                if not safe_name:
                    messages.error(request, "Nom de projet invalide.")
                else:
                    target_dir = current_path / safe_name
                    if target_dir.exists():
                        messages.error(request, "Un dossier porte deja ce nom.")
                    else:
                        try:
                            with zipfile.ZipFile(upload) as zip_file:
                                target_dir.mkdir(parents=True, exist_ok=False)
                                _safe_extract_zip(zip_file, target_dir)
                            messages.success(request, "Projet importe.")
                        except (zipfile.BadZipFile, ValueError, OSError):
                            messages.error(request, "Impossible d'importer le zip.")

        if action == "upload_folder":
            uploads = request.FILES.getlist("project_folder")
            base_name = _sanitize_name(request.POST.get("folder_name"))
            if not uploads:
                messages.error(request, "Dossier requis.")
            else:
                default_root = None
                try:
                    normalized_paths = []
                    for upload in uploads:
                        path = _normalize_upload_path(upload.name)
                        normalized_paths.append((upload, path))
                        if default_root is None and len(path.parts) > 1:
                            default_root = path.parts[0]
                except ValueError:
                    messages.error(request, "Chemin de dossier invalide.")
                    normalized_paths = []

                if normalized_paths:
                    if not base_name:
                        base_name = default_root or f"import-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
                    base_name = _sanitize_name(base_name)
                    if not base_name:
                        messages.error(request, "Nom de dossier invalide.")
                    else:
                        target_root = current_path / base_name
                        if target_root.exists():
                            messages.error(request, "Un dossier porte deja ce nom.")
                        else:
                            try:
                                for upload, path in normalized_paths:
                                    rel_parts = path.parts
                                    if default_root and rel_parts and rel_parts[0] == default_root:
                                        rel_parts = rel_parts[1:]
                                    if not rel_parts:
                                        continue
                                    rel_path = Path(*rel_parts)
                                    _safe_write_upload(target_root, rel_path, upload)
                                messages.success(request, "Dossier importe.")
                            except (ValueError, OSError):
                                messages.error(request, "Impossible d'importer ce dossier.")

        target_url = reverse_lazy("projects")
        if rel_path:
            target_url = f"{target_url}?path={quote(rel_path)}"
        return redirect(target_url)

    def _build_context(self, request):
        root = _safe_projects_root()
        root.mkdir(parents=True, exist_ok=True)
        rel_path = request.GET.get("path", "")
        try:
            current_path = _resolve_projects_path(root, rel_path)
        except ValueError:
            current_path = root
            rel_path = ""

        if not current_path.exists() or not current_path.is_dir():
            messages.error(request, "Chemin introuvable.")
            current_path = root
            rel_path = ""

        entries = []
        try:
            for entry in current_path.iterdir():
                try:
                    stat = entry.stat()
                except OSError:
                    continue
                entries.append(
                    {
                        "name": entry.name,
                        "is_dir": entry.is_dir(),
                        "size": _format_bytes(stat.st_size) if entry.is_file() else "",
                        "modified": datetime.fromtimestamp(stat.st_mtime),
                        "rel_path": str(entry.relative_to(root)),
                    }
                )
        except OSError:
            messages.error(request, "Impossible de lire ce dossier.")

        entries.sort(key=lambda item: (not item["is_dir"], item["name"].lower()))

        breadcrumbs = [{"name": "Racine", "path": ""}]
        if rel_path:
            parts = Path(rel_path).parts
            for idx, part in enumerate(parts, start=1):
                breadcrumbs.append(
                    {
                        "name": part,
                        "path": str(Path(*parts[:idx])),
                    }
                )

        context = {
            "projects_root": str(root),
            "current_path": str(current_path),
            "relative_path": rel_path,
            "entries": entries,
            "breadcrumbs": breadcrumbs,
        }
        return context


class ItemListView(LoginRequiredMixin, ListView):
    template_name = "core/item_list.html"
    model = Item
    paginate_by = 20

    def get_queryset(self):
        qs = Item.objects.select_related("category")
        item_type = self.request.GET.get("type")
        status = self.request.GET.get("status")
        category = self.request.GET.get("category")
        search = self.request.GET.get("q")
        if item_type:
            qs = qs.filter(type=item_type)
        if status:
            qs = qs.filter(status=status)
        if category:
            qs = qs.filter(category__id=category)
        if search:
            qs = qs.filter(Q(title__icontains=search) | Q(content__icontains=search))
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.all()
        context["item_types"] = Item.TYPE_CHOICES
        context["status_choices"] = Item.ALL_STATUS_CHOICES
        return context


class ItemDetailView(LoginRequiredMixin, DetailView):
    template_name = "core/item_detail.html"
    model = Item


class ItemCreateView(LoginRequiredMixin, CreateView):
    template_name = "core/item_form.html"
    form_class = ItemForm
    model = Item

    def get_initial(self):
        initial = super().get_initial()
        type_param = self.request.GET.get("type")
        if type_param in dict(Item.TYPE_CHOICES):
            initial["type"] = type_param
            initial["status"] = Item.status_choices_for(type_param)[0][0]
        return initial

    def get_success_url(self):
        messages.success(self.request, "Element cree.")
        return reverse_lazy("item_detail", kwargs={"pk": self.object.pk})


class ItemUpdateView(LoginRequiredMixin, UpdateView):
    template_name = "core/item_form.html"
    form_class = ItemForm
    model = Item

    def get_success_url(self):
        messages.success(self.request, "Element mis a jour.")
        return reverse_lazy("item_detail", kwargs={"pk": self.object.pk})


class ItemDeleteView(LoginRequiredMixin, DeleteView):
    template_name = "core/item_confirm_delete.html"
    model = Item
    success_url = reverse_lazy("dashboard")

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Element supprime.")
        return super().delete(request, *args, **kwargs)


@login_required
@require_POST
def convert_item(request, pk: int):
    item = get_object_or_404(Item, pk=pk)
    item.convert_to_project()
    item.save(update_fields=["type", "status", "updated_at"])
    messages.success(request, "Idee convertie en projet.")
    query = request.META.get("HTTP_REFERER")
    if query:
        return redirect(query)
    return redirect("item_detail", pk=pk)


@login_required
@require_POST
def move_item(request, pk: int):
    item = get_object_or_404(Item, pk=pk)

    data = {}
    if request.body:
        try:
            data = json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError:
            data = {}
    data.update(request.POST.dict())

    target_status = data.get("status")
    target_type = data.get("type", item.type)

    if not target_status:
        return JsonResponse({"ok": False, "error": "Status manquant."}, status=400)

    if target_type not in dict(Item.TYPE_CHOICES):
        return JsonResponse({"ok": False, "error": "Type invalide."}, status=400)

    if item.type == Item.TYPE_PROJECT and target_type == Item.TYPE_IDEA:
        return JsonResponse(
            {"ok": False, "error": "Conversion projet vers idee non supportee."},
            status=400,
        )

    allowed = {key for key, _ in Item.status_choices_for(target_type)}
    if target_status not in allowed:
        return JsonResponse({"ok": False, "error": "Status invalide."}, status=400)

    item.type = target_type
    item.status = target_status
    item.save(update_fields=["type", "status", "updated_at"])

    return JsonResponse(
        {
            "ok": True,
            "id": item.pk,
            "status": item.status,
            "type": item.type,
        }
    )


class CategoryListView(LoginRequiredMixin, ListView):
    template_name = "core/category_list.html"
    model = Category


class CategoryCreateView(LoginRequiredMixin, CreateView):
    template_name = "core/category_form.html"
    form_class = CategoryForm
    model = Category

    def get_success_url(self):
        messages.success(self.request, "Categorie creee.")
        return reverse_lazy("category_list")


class CategoryUpdateView(LoginRequiredMixin, UpdateView):
    template_name = "core/category_form.html"
    form_class = CategoryForm
    model = Category

    def get_success_url(self):
        messages.success(self.request, "Categorie mise a jour.")
        return reverse_lazy("category_list")


class CategoryDeleteView(LoginRequiredMixin, DeleteView):
    template_name = "core/category_confirm_delete.html"
    model = Category
    success_url = reverse_lazy("category_list")

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Categorie supprimee.")
        return super().delete(request, *args, **kwargs)

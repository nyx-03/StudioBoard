from django.db import models
from django.contrib.auth.models import User

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Board(TimeStampedModel):
    """
    Un tableau Kanban (ex: 'Idées', 'Projets', etc.)
    """
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="boards")

    def __str__(self) -> str:
        return self.name

class Column(TimeStampedModel):
    """
    Une colonne d'un board (ex: 'Idées', 'A creuser', 'Validées')
    """
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name="columns")
    name = models.CharField(max_length=80)
    order = models.PositiveIntegerField(default=0)

    KIND_NORMAL = "normal"
    KIND_VALIDATED = "validated"
    KIND_ARCHIVED = "archived"

    KIND_CHOICES = [
        (KIND_NORMAL, "Normale"),
        (KIND_VALIDATED, "Validée"),
        (KIND_ARCHIVED, "Archivée"),
    ]

    kind = models.CharField(
        max_length=12,
        choices=KIND_CHOICES,
        default=KIND_NORMAL,
        help_text="Rôle fonctionnel de la colonne (logique métier)"
    )

    class Meta:
        ordering = ["order", "id"]
        constraints = [
            models.UniqueConstraint(fields=["board", "name"], name="uniq_column_name_per_board"),
            models.UniqueConstraint(fields=["board", "order"], name="uniq_column_order_per_board"),
        ]

    def __str__(self) -> str:
        return f"{self.board.name} / {self.name}"

class Tag(TimeStampedModel):
    """
    Tag global (ex: 'tech', 'marketing', 'produit'
    """
    name = models.CharField(max_length=40, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class IdeaStatus(models.TextChoices):
    DRAFT = "draft", "Brouillon"
    ACTIVE = "active", "Active"
    ARCHIVED = "archived", "Archivée"

class Idea(TimeStampedModel):
    """
    Une carte (idée) qui vit dans une colonne
    """

    column = models.ForeignKey(Column, on_delete=models.CASCADE, related_name="ideas")

    converted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date de conversion de l'idée en projet (si applicable).",
    )

    title = models.CharField(max_length=180)
    body_md = models.TextField(blank=True)
    status = models.CharField(max_length=12, choices=IdeaStatus.choices, default=IdeaStatus.ACTIVE)


    position = models.PositiveIntegerField(default=0)

    tags = models.ManyToManyField(Tag, blank=True, related_name="ideas")

    impact = models.PositiveSmallIntegerField(default=0)  # 0..5 par ex.
    next_action = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["position", "id"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["column", "position"]),
        ]

    def __str__(self) -> str:
        return self.title


# Extension 'Projet' pour une idée convertie en projet
class IdeaProject(TimeStampedModel):
    """
    Extension 'Projet' attachée à une Idea convertie.
    Une idée devient un projet quand cette extension existe.
    """
    idea = models.OneToOneField(
        Idea,
        on_delete=models.CASCADE,
        related_name="project",
        help_text="Idea source de ce projet",
    )

    goals = models.TextField(blank=True, help_text="Objectifs (Markdown autorisé).")
    scope = models.TextField(blank=True, help_text="Périmètre / inclusions-exclusions.")
    definition_of_done = models.TextField(blank=True, help_text="Définition de terminé (DoD).")
    due_date = models.DateField(null=True, blank=True, help_text="Échéance cible (optionnelle).")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Project: {self.idea.title}"


class IdeaTemplate(models.Model):
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    body_md = models.TextField(help_text="Contenu Markdown du template")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

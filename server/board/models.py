from django.db import models

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

    def __str__(self) -> self:
        return self.name

class Column(TimeStampedModel):
    """
    Une colonne d'un board (ex: 'Idées', 'A creuser', 'Validées')
    """
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name="columns")
    name = models.CharField(max_length=80)
    order = models.PositiveIntegerField(default=0)

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

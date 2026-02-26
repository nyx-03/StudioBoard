from django.core.exceptions import ValidationError
from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    color = models.CharField(
        max_length=7,
        blank=True,
        help_text="Hex color like #FFAA00",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Item(models.Model):
    TYPE_IDEA = "idea"
    TYPE_PROJECT = "project"

    STATUS_DRAFT = "draft"
    STATUS_THINKING = "thinking"
    STATUS_ABANDONED = "abandoned"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_TESTING = "testing"
    STATUS_VALIDATED = "validated"
    STATUS_DONE = "done"

    TYPE_CHOICES = [
        (TYPE_IDEA, "Idee"),
        (TYPE_PROJECT, "Projet"),
    ]

    IDEA_STATUSES = [
        (STATUS_DRAFT, "Brouillon"),
        (STATUS_THINKING, "En reflexion"),
        (STATUS_ABANDONED, "Abandonne"),
    ]

    PROJECT_STATUSES = [
        (STATUS_IN_PROGRESS, "En cours"),
        (STATUS_TESTING, "Test"),
        (STATUS_VALIDATED, "Validee"),
        (STATUS_DONE, "Termine"),
    ]

    ALL_STATUS_CHOICES = IDEA_STATUSES + PROJECT_STATUSES

    title = models.CharField(max_length=200)
    content = models.TextField(blank=True)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default=TYPE_IDEA)
    status = models.CharField(max_length=20, choices=ALL_STATUS_CHOICES, default=STATUS_DRAFT)
    category = models.ForeignKey(
        Category,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="items",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        return self.title

    @property
    def is_idea(self) -> bool:
        return self.type == self.TYPE_IDEA

    @property
    def is_project(self) -> bool:
        return self.type == self.TYPE_PROJECT

    @classmethod
    def status_choices_for(cls, item_type: str):
        if item_type == cls.TYPE_PROJECT:
            return cls.PROJECT_STATUSES
        return cls.IDEA_STATUSES

    def clean(self) -> None:
        allowed = {key for key, _ in self.status_choices_for(self.type)}
        if self.status not in allowed:
            raise ValidationError({"status": "Status invalide pour ce type."})

    def convert_to_project(self) -> None:
        if self.type == self.TYPE_PROJECT:
            return
        self.type = self.TYPE_PROJECT
        if self.status not in {key for key, _ in self.PROJECT_STATUSES}:
            self.status = self.STATUS_IN_PROGRESS

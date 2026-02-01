from django import forms
from .models import Column, Idea, IdeaTemplate


class IdeaForm(forms.ModelForm):
    """
    Formulaire create/edit d'une idée.
    Les tags sont saisis en texte libre: "python, django, marketing".
    """
    tags_text = forms.CharField(
        required=False,
        label="Tags",
        help_text="Sépare par des virgules (ex: python, django, marketing)",
        widget=forms.TextInput(attrs={"placeholder": "python, django, marketing"}),
    )

    class Meta:
        model = Idea
        fields = ["title", "column", "impact", "next_action", "body_md", "status"]
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Titre de l'idée"}),
            "next_action": forms.TextInput(attrs={"placeholder": "Ex: faire un wireframe"}),
            "body_md": forms.Textarea(attrs={"rows": 8, "placeholder": "Notes (Markdown)…"}),
        }
        labels = {
            "title": "Titre",
            "column": "Colonne",
            "impact": "Impact (0–5)",
            "next_action": "Prochaine action",
            "body_md": "Description (Markdown)",
            "status": "Statut",
        }

    def __init__(self, *args, **kwargs):
        board = kwargs.pop("board", None)
        super().__init__(*args, **kwargs)

        # Colonnes restreintes au board
        if board is not None:
            self.fields["column"].queryset = Column.objects.filter(board=board).order_by("order", "id")
        else:
            self.fields["column"].queryset = Column.objects.none()

        # Garde-fous
        self.fields["impact"].min_value = 0
        self.fields["impact"].max_value = 5

        # Pré-remplir tags_text si on édite une idée existante
        if self.instance and self.instance.pk:
            current = list(self.instance.tags.values_list("name", flat=True))
            self.fields["tags_text"].initial = ", ".join(current)

class IdeaCreateForm(IdeaForm):
    template_id = forms.ModelChoiceField(
        queryset=IdeaTemplate.objects.none(),
        required=False,
        empty_label="(Aucun template)",
        label="Template",
        help_text="Optionnel. Pré-remplit la description en Markdown à la création.",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["template_id"].queryset = (
            IdeaTemplate.objects.filter(is_active=True).order_by("name")
        )
        # À la création, on ne force pas le statut : on mettra une valeur par défaut côté modèle/vue.
        if "status" in self.fields:
            self.fields["status"].required = False


class IdeaTemplateFromIdeaForm(forms.Form):
    name = forms.CharField(
        max_length=120,
        label="Nom du template",
        widget=forms.TextInput(attrs={"placeholder": "Ex: Cahier des charges / module / landing"}),
    )
    is_active = forms.BooleanField(
        required=False,
        initial=True,
        label="Activer ce template",
    )
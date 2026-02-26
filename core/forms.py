from django import forms

from .models import Category, Item


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "description", "color"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "input"}),
            "description": forms.Textarea(attrs={"class": "input", "rows": 4}),
            "color": forms.TextInput(attrs={"class": "input", "placeholder": "#FFAA00"}),
        }


class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ["title", "type", "status", "category", "content"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "input"}),
            "type": forms.Select(attrs={"class": "input"}),
            "status": forms.Select(attrs={"class": "input", "data-status-select": "true"}),
            "category": forms.Select(attrs={"class": "input"}),
            "content": forms.Textarea(attrs={"class": "input", "rows": 8}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        type_value = (
            self.data.get("type")
            or self.initial.get("type")
            or (self.instance.type if self.instance.pk else None)
        )
        if type_value:
            self.fields["status"].choices = Item.status_choices_for(type_value)

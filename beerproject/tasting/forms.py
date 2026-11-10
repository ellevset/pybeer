from django import forms
from .models import Vote


class VoteForm(forms.ModelForm):
    class Meta:
        model = Vote
        fields = ["score", "comment"]
        widgets = {
            "score": forms.Select(choices=[(n, n) for n in range(1, 6)]),
            "comment": forms.Textarea(attrs={"rows": 3}),
        }

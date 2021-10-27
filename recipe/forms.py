from django import forms

from recipe.models import Recipe

class RejectReasonForm(forms.Form):

    rejection_reason = forms.CharField(
        required=True,
        widget=forms.Textarea,
        max_length=200
    )

    def save(self, recipe):
        recipe.status = Recipe.Status.REJECTED
        recipe.rejection_reason = self.cleaned_data['rejection_reason']
        recipe.save()

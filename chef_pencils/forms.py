from django import forms

from chef_pencils.models import ChefPencilRecord


class RejectReasonForm(forms.Form):

    rejection_reason = forms.CharField(
        required=True,
        widget=forms.Textarea,
        max_length=200
    )

    def save(self, cp):
        cp.status = ChefPencilRecord.Status.REJECTED
        cp.rejection_reason = self.cleaned_data['rejection_reason']
        cp.save()

from django import forms


class RejectionForm(forms.Form):
    rejection_note = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}))

# forms.py

from django import forms
from .models import ReceiptFile

class ReceiptFileForm(forms.ModelForm):
    file = forms.FileField(required=False)
    class Meta:
        model = ReceiptFile
        fields = ['file']
        class Media:
            css = {
                'all': ('https://maxcdn.bootstrapcdn.com/bootstrap/3.4.1/css/bootstrap.min.css',)
            }

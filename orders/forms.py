from django import forms
from django.utils import timezone


class OrderForm(forms.Form):
    shipment_date = forms.DateField(
        label='Дата отгрузки',
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
    )
    comment = forms.CharField(
        label='Комментарий',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control', 'rows': 3,
            'placeholder': 'Необязательный комментарий...',
        }),
    )

    def clean_shipment_date(self):
        date = self.cleaned_data['shipment_date']
        if date < timezone.now().date():
            raise forms.ValidationError('Дата не может быть прошедшей.')
        return date


class ManagerDeleteForm(forms.Form):
    reason = forms.CharField(
        label='Причина удаления',
        widget=forms.Textarea(attrs={
            'class': 'form-control', 'rows': 3,
            'placeholder': 'Укажите причину...',
        }),
    )

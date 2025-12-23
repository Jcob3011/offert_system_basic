from django import forms
from django.forms import inlineformset_factory
from .models import Offer, OfferItem

# 1. Formularz Główny 
class OfferForm(forms.ModelForm):
    class Meta:
        model = Offer
        # offer_number i total_price wyliczymy sami w backendzie.
        fields = ['client_name', 'client_email', 'description', 'status', 'external_file']
        
        labels = {
            'client_name': 'Nazwa Klienta',
            'client_email': 'Email',
            'description': 'Opis / Zakres prac',
            'status': 'Status',
            'external_file': 'Archiwalny PDF (opcjonalnie)',
        }
        widgets = {
            'client_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'np. Firma XYZ'}),
            'client_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'kontakt@klient.pl'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'external_file': forms.FileInput(attrs={'class': 'form-control'}),
        }

# 2. Formularz Pozycji (Payload)
class OfferItemForm(forms.ModelForm):
    class Meta:
        model = OfferItem
        fields = ['description', 'quantity', 'price_per_unit']
        
        widgets = {
            'description': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Nazwa usługi/produktu'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control text-end', 
                'step': '1', 
                'placeholder': '0'
            }),
            'price_per_unit': forms.NumberInput(attrs={
                'class': 'form-control text-end', 
                'step': '0.01', 
                'placeholder': '0.00'
            }),
        }
# 3. FormSet - Fabryka łączenia
OfferItemFormSet = inlineformset_factory(
    Offer, OfferItem, form=OfferItemForm,
    extra=1,       # Jeden pusty wiersz na start
    can_delete=True # Pozwalamy usuwać wiersze
)
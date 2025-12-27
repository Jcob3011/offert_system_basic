from django import forms
from django.forms import inlineformset_factory
from .models import Offer, OfferItem


# 1. Formularz Główny
class OfferForm(forms.ModelForm):
    class Meta:
        model = Offer
        # UWAGA: Tutaj wymieniamy pola, które user ma widzieć i wypełnić.
        fields = [
            'seller',
            'client',
            'description',
            'status',
            'validity_days',
            'payment_deadline_days',
            'payment_method',
            'currency_rate',
            'external_file'
        ]

        labels = {
            'seller': 'Wystawca (Spółka)',
            'client': 'Wybierz Klienta',
            'description': 'Opis / Wstęp do oferty',
            'status': 'Status początkowy',
            'validity_days': 'Ważność (dni)',
            'payment_deadline_days': 'Termin płatności (dni)',
            'payment_method': 'Sposób płatności',
            'currency_rate': 'Kurs EUR (opcjonalnie)',
            'external_file': 'Archiwalny PDF (opcjonalnie)',
        }

        widgets = {
            'seller': forms.Select(attrs={'class': 'form-select'}),
            'client': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            # Pola liczbowe
            'validity_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'payment_deadline_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'currency_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),

            'external_file': forms.FileInput(attrs={'class': 'form-control'}),
        }


# 2. Formularz Pozycji (Payload)
class OfferItemForm(forms.ModelForm):
    class Meta:
        model = OfferItem
        fields = ['description', 'quantity', 'price_per_unit', 'price_in_eur']
        widgets = {
            'description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nazwa usługi/produktu'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control text-end',
                'step': '1',
                'placeholder': '1'
            }),
            'price_per_unit': forms.NumberInput(attrs={
                'class': 'form-control text-end',
                'step': '0.01',
                'placeholder': 'PLN'
            }),
            'price_in_eur': forms.NumberInput(attrs={
                'class': 'form-control text-end',
                'step': '0.01',
                'placeholder': 'EUR'
            }),
        }


# 3. FormSet - Fabryka łączenia
OfferItemFormSet = inlineformset_factory(
    Offer, OfferItem, form=OfferItemForm,
    extra=1,  # Jeden pusty wiersz na start
    can_delete=True  # Pozwalamy usuwać wiersze
)

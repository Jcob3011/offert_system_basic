from django.db import models
from ckeditor.fields import RichTextField
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from datetime import timedelta
from django.contrib.auth.models import User


# --- NOWE MODELE (CRM) ---

class Company(models.Model):
    name = models.CharField(max_length=200, verbose_name="Nazwa Firmy")
    nip = models.CharField(max_length=20, blank=True, null=True, verbose_name="NIP")
    address = models.TextField(verbose_name="Adres", blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Firma"
        verbose_name_plural = "Baza Firm"


class Client(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='employees', verbose_name="Firma")
    first_name = models.CharField(max_length=100, verbose_name="Imię")
    last_name = models.CharField(max_length=100, verbose_name="Nazwisko")
    email = models.EmailField(verbose_name="Email")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Telefon")
    position = models.CharField(max_length=100, blank=True,
                                verbose_name="Stanowisko")  # np. "Dyrektor IT" vs "Serwisant"

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.company.name})"

    class Meta:
        verbose_name = "Klient / Kontakt"
        verbose_name_plural = "Baza Klientów"


class Seller(models.Model):
    name = models.CharField(max_length=200, verbose_name="Nazwa Naszej Firmy")
    nip = models.CharField(max_length=20, verbose_name="NIP")
    address = models.TextField(verbose_name="Adres")
    email = models.EmailField(verbose_name="Email kontaktowy", blank=True)
    phone = models.CharField(max_length=20, verbose_name="Telefon", blank=True)
    bank_account = models.CharField(max_length=50, verbose_name="Konto Bankowe", blank=True)

    # Logo - ważne! Wymaga biblioteki Pillow
    logo = models.ImageField(upload_to='company_logos/', verbose_name="Logo", blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Nazwa Firmy"
        verbose_name_plural = "Nasze Firmy"


# --- ZMODYFIKOWANY MODEL OFERTY ---

class Offer(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', _('Robocza')
        PENDING = 'pending', _('Oczekuje na akceptację')
        IN_CONSULTATION = 'consultation', _('Konsultacja z Seniorem')  # NOWOŚĆ (5)
        APPROVED = 'approved', _('Zatwierdzona')
        SENT = 'sent', _('Wysłana')
        REJECTED = 'rejected', _('Odrzucona')

    class PaymentMethod(models.TextChoices):  # NOWOŚĆ (6)
        TRANSFER = 'transfer', _('Przelew tradycyjny')
        SPLIT_PAYMENT = 'split', _('Przelew (Split Payment)')
        CASH = 'cash', _('Gotówka')
        CARD = 'card', _('Karta płatnicza')

    # Podstawowe
    seller = models.ForeignKey(Seller, on_delete=models.PROTECT, verbose_name="Wystawca", null=True)
    offer_number = models.CharField(max_length=50, unique=True, verbose_name="Numer oferty")
    # ZMIANA: Zamiast wpisywać ręcznie, wybieramy z bazy (Foreign Key) (1, 2)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, verbose_name="Klient", null=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT, verbose_name="Status")
    description = RichTextField(null=True, blank=True, help_text="Wstęp/Opis oferty")
    # Finanse
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Suma PLN")
    # Waluty (7) - Manualne sterowanie na początek
    currency_rate = models.DecimalField(max_digits=6, decimal_places=4, default=1.0000,
                                        verbose_name="Kurs EUR (dla informacji)")

    # Terminy i Płatności (3, 6)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    validity_days = models.PositiveIntegerField(default=14, verbose_name="Ważność oferty (dni)")
    payment_deadline_days = models.PositiveIntegerField(default=7, verbose_name="Termin płatności (dni)")
    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices, default=PaymentMethod.TRANSFER,
                                      verbose_name="Metoda płatności")

    # Powód odrzucenia (4)
    rejection_reason = models.TextField(blank=True, null=True, verbose_name="Powód odrzucenia (CEO)")

    external_file = models.FileField(upload_to='offers_archive/', null=True, blank=True, verbose_name="Archiwalny PDF")
    # Kto utworzył oferte
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Utworzył")

    def update_total(self):
        """
        Przelicza sumę oferty na podstawie pozycji.
        """
        # 1. Pobieramy wszystkie pozycje tej oferty
        offer_items = self.items.all()

        # 2. Sumujemy (używając property total_price z items)
        new_total = sum(item.total_price for item in offer_items)

        # 3. Zapisujemy wynik w bazie
        self.total_price = new_total
        # Używamy update_fields, żeby nie nadpisywać innych pól (optymalizacja)
        self.save(update_fields=['total_price'])

    def __str__(self):
        return f"{self.offer_number}"

    # Metoda pomocnicza do szablonu - kiedy wygasa?
    @property
    def valid_until_date(self):
        return self.created_at.date() + timedelta(days=self.validity_days)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Oferta"
        verbose_name_plural = "Baza Ofert"


# --- POZYCJE OFERTY (Tu też mała zmiana pod waluty) ---

class OfferItem(models.Model):
    offer = models.ForeignKey(Offer, on_delete=models.CASCADE, related_name='items')
    description = models.CharField(max_length=200, verbose_name="Nazwa produktu")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Ilość")

    # Cena jednostkowa w PLN (ostateczna)
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Cena jedn. PLN")

    # Opcjonalnie: Oryginalna cena w EUR (tylko do podglądu)
    price_in_eur = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                       verbose_name="Cena katalogowa EUR")

    @property
    def total_price(self):
        return self.quantity * self.price_per_unit

    def __str__(self):
        return self.description


# --- SYGNAŁY BEZ ZMIAN ---
@receiver(post_save, sender=OfferItem)
@receiver(post_delete, sender=OfferItem)
def recalculate_offer_total(sender, instance, **kwargs):
    offer = instance.offer
    offer.update_total()

from django.db import models
from ckeditor.fields import RichTextField
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

class Offer(models.Model):
    class Status(models.TextChoices): 
        DRAFT = 'draft', _('Robocza')
        PENDING = 'pending', _('Oczekuje na akceptację')
        APPROVED = 'approved', _('Zatwierdzona')
        SENT = 'sent', _('Wysłana')
        REJECTED = 'rejected', 'Odrzucona'
        
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.DRAFT
    )

    offer_number = models.CharField(max_length=20, unique=True, verbose_name="Numer oferty")
    client_name = models.CharField(max_length=100, verbose_name="Klient")
    client_email = models.EmailField(verbose_name="Email klienta")
    description = RichTextField(null=True, blank=True, help_text="Opis oferty widoczny na PDF")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Cena całkowita")
    status = models.CharField(max_length=10, choices=Status, default='draft', verbose_name="Status")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    external_file = models.FileField(
        upload_to='offers_archive/', 
        null=True, 
        blank=True, 
        verbose_name="Wgrany plik PDF (dla starych ofert)"
    )
    
    
    def update_total(self):
        # 1. Pobieramy dzieci. 
        offer_items = self.items.all()
        
        # 2. Sumujemy. 
        new_total = sum(item.total_price for item in offer_items)
        
        # 3. Zapisujemy wynik w tabeli routingu (bazie danych)
        self.total_price = new_total
        self.save(update_fields=['total_price'])

    def __str__(self):
        return f"Oferta {self.offer_number} dla {self.client_name}"
    
    
    
    class Meta:
        verbose_name = "Oferta"          # Jak nazwać jeden obiekt
        verbose_name_plural = "Oferty"   # Jak nazwać listę w menu
        ordering = ['-id']               # Przy okazji: najnowsze oferty będą na górze listy
        
    def css_class(self):
        """Pomocnik dla Frontendu: Mapuje status na klasę CSS"""
        if self.status == self.Status.DRAFT:
            return 'status-draft'
        elif self.status == self.Status.PENDING:
            return 'status-pending'
        elif self.status == self.Status.APPROVED:
            return 'status-approved'
        elif self.status == self.Status.REJECTED:
            return 'status-rejected'
        return 'status-draft'

class OfferItem(models.Model):
    offer = models.ForeignKey(Offer, on_delete=models.CASCADE, related_name='items')
    description = models.CharField(max_length=200, verbose_name="Nazwa Usługi/Produktu")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Ilość")
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Cena jedn.")

    # To zostawiamy tylko dla wygody wyświetlania (nic nie zapisuje w bazie)
    @property
    def total_price(self):
        return self.quantity * self.price_per_unit

    def __str__(self):
        return self.description

# --- SYGNAŁY (AUTOMATYKA) ---

@receiver(post_save, sender=OfferItem)
@receiver(post_delete, sender=OfferItem)
def recalculate_offer_total(sender, instance, **kwargs):
    """
    Trigger: Uruchamia się po dodaniu, edycji lub usunięciu OfferItem.
    Action: Przelicza sumę w ofercie nadrzędnej.
    """
    # instance to ten konkretny OfferItem, który właśnie zmieniliśmy
    offer = instance.offer
    
    # Odpalamy przeliczanie w rodzicu
    offer.update_total()
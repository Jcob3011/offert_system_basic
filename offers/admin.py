from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Offer, OfferItem, Client, Company, Seller
from import_export.admin import ImportExportModelAdmin

# Branding
admin.site.site_header = "System Ofertowy"
admin.site.site_title = "Panel Zarządzania"
admin.site.index_title = "Ofertowanie"


# --- Modele ---

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'nip', 'address']
    search_fields = ['name', 'nip']


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'company', 'email', 'position']
    list_filter = ['company']
    search_fields = ['last_name', 'email', 'company__name']  # Szukanie po nazwisku i firmie


@admin.register(Seller)
class SellerAdmin(admin.ModelAdmin):
    list_display = ['name', 'nip', 'email']


# --- KONIEC MODELI ---

class OfferItemInline(admin.TabularInline):
    model = OfferItem
    extra = 0

    # Blokada edycji pól, jeśli nie DRAFT (ACL)
    def get_readonly_fields(self, request, obj=None):
        if obj and obj.status != Offer.Status.DRAFT:
            return [f.name for f in self.model._meta.fields]
        return []

    def has_add_permission(self, request, obj=None):
        if obj and obj.status != Offer.Status.DRAFT:
            return False
        return super().has_add_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj and obj.status != Offer.Status.DRAFT:
            return False
        return super().has_delete_permission(request, obj)


@admin.register(Offer)
class OfferAdmin(ImportExportModelAdmin):
    inlines = [OfferItemInline]
    actions = ['make_pending', 'make_draft', 'make_approved']
    list_display = ('offer_number', 'client', 'total_price', 'status_colored', 'pdf_button', 'created_at')
    list_display_links = ['offer_number']  # Linkujemy tylko numer, żeby nie kliknąć przypadkiem w klienta
    list_filter = ['status', 'created_at', 'client__company']  # Filtr po firmie!

    # ZMIANA: Szukanie "głębokie" (Deep Packet Inspection)
    # client__last_name -> szukaj w tabeli Client po polu last_name
    # client__company__name -> szukaj w tabeli Company po polu name
    search_fields = ['offer_number', 'client__last_name', 'client__company__name', 'client__email']

    list_per_page = 20

    # --- UI ---

    def status_colored(self, obj):
        # Aktualizacja palety kolorów dla nowych statusów
        colors = {
            Offer.Status.DRAFT: 'gray',
            Offer.Status.PENDING: 'orange',
            Offer.Status.IN_CONSULTATION: 'blue',
            Offer.Status.APPROVED: 'green',
            Offer.Status.SENT: 'purple',
            Offer.Status.REJECTED: 'red',
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<b style="color: {};">{}</b>',
            color,
            obj.get_status_display()
        )

    status_colored.short_description = "Status"

    def pdf_button(self, obj):

        url = reverse('offer_pdf', args=[obj.pk])
        return format_html(
            '<a class="button" href="{}" target="_blank">PDF</a>',
            url
        )

    pdf_button.short_description = "Pobierz"

    # --- ACL / Readonly ---

    def get_readonly_fields(self, request, obj=None):
        # Zablokowane pola systemowe
        default_readonly = ['total_price', 'offer_number', 'created_at', 'updated_at']

        if not obj:
            return default_readonly

        # Jeśli status inny niż DRAFT i ODRZUCONA -> blokujemy wszystko
        # Pozwalamy edytować ODRZUCONĄ, żeby można było poprawić błędy
        if obj.status not in [Offer.Status.DRAFT, Offer.Status.REJECTED]:
            return [f.name for f in self.model._meta.fields]

        return default_readonly

    # --- ACTIONS (Maszyna Stanów) ---

    @admin.action(description='Prześlij do akceptacji (-> PENDING)')
    def make_pending(self, request, queryset):
        # Możemy wysłać tylko DRAFY lub ODRZUCONE (po poprawce)
        updated = queryset.filter(status__in=[Offer.Status.DRAFT, Offer.Status.REJECTED]).update(
            status=Offer.Status.PENDING)
        self.message_user(request, f"Wysłano do akceptacji: {updated} ofert.")

    @admin.action(description='Cofnij do edycji (-> DRAFT)')
    def make_draft(self, request, queryset):
        updated = queryset.update(status=Offer.Status.DRAFT)
        self.message_user(request, f"Przywrócono do edycji: {updated} ofert.")

    @admin.action(description='Zatwierdź (-> APPROVED)')
    def make_approved(self, request, queryset):
        # Zatwierdzamy tylko te oczekujące
        updated = queryset.filter(status=Offer.Status.PENDING).update(status=Offer.Status.APPROVED)
        self.message_user(request, f"Zatwierdzono: {updated} ofert.")

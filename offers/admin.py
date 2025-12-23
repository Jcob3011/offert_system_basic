from django.contrib import admin
from django.utils.html import format_html # Do kolorowania HTML
from django.urls import reverse # Do generowania linków
from .models import Offer, OfferItem
from import_export.admin import ImportExportModelAdmin

# Branding
admin.site.site_header = "System Ofertowy"
admin.site.site_title = "Panel Zarządzania"
admin.site.index_title = "Ofertowanie"



class OfferItemInline(admin.TabularInline):
    model = OfferItem
    extra = 0
    
    # Blokada edycji pól, jeśli nie DRAFT
    def get_readonly_fields(self, request, obj=None):
        if obj and obj.status != Offer.Status.DRAFT:
            return [f.name for f in self.model._meta.fields]
        return []

    # Blokada dodawania
    def has_add_permission(self, request, obj=None):
        if obj and obj.status != Offer.Status.DRAFT:
            return False
        return super().has_add_permission(request, obj)

    # Blokada usuwania
    def has_delete_permission(self, request, obj=None):
        if obj and obj.status != Offer.Status.DRAFT:
            return False
        return super().has_delete_permission(request, obj)

@admin.register(Offer)
class OfferAdmin(ImportExportModelAdmin):
    inlines = [OfferItemInline]
    # POPRAWKA: Dodałem 'make_approved' do listy akcji
    actions = ['make_pending', 'make_draft', 'make_approved']
    
    # ZMIANA: Dodajemy nasze nowe "wirtualne kolumny": status_colored i pdf_button
    list_display = ('offer_number', 'client_name', 'total_price', 'status_colored', 'pdf_button', 'created_at')
    
    list_display_links = ['offer_number', 'client_name']
    list_filter = ['status', 'created_at']
    search_fields = ['offer_number', 'client_name', 'client_email']
    list_per_page = 20
    
    
    
    # --- NOWE FUNKCJE UI ---

    # 1. Kolorowy status 
    def status_colored(self, obj):
        colors = {
            Offer.Status.DRAFT: 'gray',
            Offer.Status.PENDING: 'orange',
            Offer.Status.APPROVED: 'green',
            Offer.Status.REJECTED: 'red',
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<b style="color: {};">{}</b>', 
            color, 
            obj.get_status_display()
        )
    status_colored.short_description = "Status" # Nazwa kolumny

    # 2. Przycisk PDF (Direct Link)
    def pdf_button(self, obj):
        url = reverse('offer_pdf', args=[obj.pk])
        return format_html(
            '<a class="button" href="{}" target="_blank">Pobierz PDF</a>', 
            url
        )
    pdf_button.short_description = "Akcje"

    # --- KONIEC UI ---

    def get_readonly_fields(self, request, obj=None):
        # Domyślnie total_price i offer_number zawsze zablokowane
        default_readonly = ['total_price', 'offer_number']
        
        if not obj:
            return default_readonly

        # Jeśli status inny niż DRAFT -> blokujemy wszystko
        if obj.status != Offer.Status.DRAFT:
            return [f.name for f in self.model._meta.fields]
            
        return default_readonly

    # --- ACTIONS ---
    
    @admin.action(description='Prześlij do akceptacji (-> PENDING)')
    def make_pending(self, request, queryset):
        rows_updated = queryset.update(status=Offer.Status.PENDING)
        self.message_user(request, f"Oznaczono {rows_updated} ofert jako PENDING.")

    @admin.action(description='Cofnij do edycji (-> DRAFT)')
    def make_draft(self, request, queryset):
        rows_updated = queryset.update(status=Offer.Status.DRAFT)
        self.message_user(request, f"Przywrócono {rows_updated} ofert do DRAFT.")
        
    @admin.action(description='Zatwierdź (-> APPROVED)')
    def make_approved(self, request, queryset):
        rows_updated = queryset.update(status=Offer.Status.APPROVED)
        self.message_user(request, f"Zatwierdzono {rows_updated} ofert.")
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
import uuid
from .models import Offer, OfferItem
from .forms import OfferForm, OfferItemFormSet
import weasyprint
from django.http import HttpResponse, FileResponse
from django.template.loader import render_to_string
from datetime import timedelta

# --- WIDOK: KAFELKI (DASHBOARD) ---
@login_required
def home(request):
    return render(request, 'offers/home.html')

# --- WIDOK: LISTA OFERT ---
@login_required
def offer_list(request):
    offers = Offer.objects.all().order_by('-created_at')
    return render(request, 'offers/offer_list.html', {'offers': offers})

# --- WIDOK: SZCZEGÓŁY OFERTY ---
@login_required
def offer_detail(request, pk):
    offer = get_object_or_404(Offer, pk=pk)
    return render(request, 'offers/offer_details.html', {'offer': offer})

# --- WIDOK: TWORZENIE NOWEJ OFERTY ---
@login_required
def offer_create(request):
    if request.method == 'POST':
        form = OfferForm(request.POST, request.FILES)
        
        if form.is_valid():
            offer = form.save(commit=False)
            
            # Generowanie unikalnego numeru
            timestamp = timezone.now().strftime("%Y%m%d")
            unique_id = str(uuid.uuid4())[:4].upper()
            offer.offer_number = f"OF/{timestamp}/{unique_id}"
            
            offer.save() # Zapisujemy, żeby mieć ID
            
            # Podpinamy produkty pod ofertę
            formset = OfferItemFormSet(request.POST, instance=offer)
            
            if formset.is_valid():
                formset.save()
                
                # Przeliczanie sumy (korzystamy z related_name='items')
                total = 0
                for item in offer.items.all():
                    total += item.total_price
                
                offer.total_price = total
                offer.save()

                return redirect('offer_detail', pk=offer.pk)
            else:
                # BŁĄD W PRODUKTACH
                print("--- BŁĄD FORMSETU (PRODUKTY) ---")
                print(formset.errors)
                offer.delete() # Usuwamy pustą ofertę
        else:
            # BŁĄD W NAGŁÓWKU
            print("--- BŁĄD FORMULARZA GŁÓWNEGO ---")
            print(form.errors)
            
    else:
        form = OfferForm()
        formset = OfferItemFormSet()

    return render(request, 'offers/offer_create.html', {
        'form': form,
        'formset': formset
    })

# --- WIDOK: EDYCJA OFERTY ---
@login_required
def offer_edit(request, pk):
    offer = get_object_or_404(Offer, pk=pk)
    
    if request.method == 'POST':
        form = OfferForm(request.POST, request.FILES, instance=offer)
        formset = OfferItemFormSet(request.POST, instance=offer)
        
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            
            # Przeliczamy sumę ponownie
            total = 0
            for item in offer.items.all():
                total += item.total_price
            
            offer.total_price = total
            offer.save()
            
            return redirect('offer_detail', pk=offer.pk)
        else:
            print("--- BŁĄD EDYCJI ---")
            print("Form errors:", form.errors)
            print("Formset errors:", formset.errors)
            
    else:
        form = OfferForm(instance=offer)
        formset = OfferItemFormSet(instance=offer)

    return render(request, 'offers/offer_create.html', {
        'form': form,
        'formset': formset,
        'offer': offer
    })

# --- WIDOK: PDF (jeśli go masz) ---
from datetime import timedelta # <--- Pamiętaj o imporcie na górze pliku!

@login_required
def offer_pdf(request, pk):
    offer = get_object_or_404(Offer, pk=pk)

    if offer.external_file:
        try:
            return FileResponse(offer.external_file.open('rb'), content_type='application/pdf')
        except FileNotFoundError:
            pass 

    # --- NOWOŚĆ: Przygotowanie dat w Pythonie ---
    # Dzięki temu w HTML wpiszemy tylko prostą zmienną
    ctx_created_date = offer.created_at.strftime('%Y-%m-%d')
    
    # Obliczamy termin ważności (np. +14 dni)
    expiration_date = offer.created_at + timedelta(days=14)
    ctx_valid_until = expiration_date.strftime('%Y-%m-%d')

    # Pakujemy dane do kontekstu
    context = {
        'offer': offer,
        'created_date': ctx_created_date, # Gotowy napis: "2023-12-22"
        'valid_until': ctx_valid_until,   # Gotowy napis: "2024-01-05"
    }
    
    html_string = render_to_string('offers/offer_pdf.html', context)
    
    html = weasyprint.HTML(string=html_string, base_url=request.build_absolute_uri())
    pdf_file = html.write_pdf()
    
    response = HttpResponse(pdf_file, content_type='application/pdf')
    safe_filename = offer.offer_number.replace('/', '_')
    response['Content-Disposition'] = f'inline; filename="Oferta_{safe_filename}.pdf"'
    
    return response
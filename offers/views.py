from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
import uuid
from django.conf import settings
from .models import Offer, OfferItem
from .forms import OfferForm, OfferItemFormSet
from weasyprint import HTML, CSS
from django.http import HttpResponse, FileResponse
from django.template.loader import render_to_string
from datetime import timedelta
from django.contrib import messages
import os


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
            offer.created_by = request.user

            offer.save()  # Zapisujemy, żeby mieć ID

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
                offer.delete()  # Usuwamy pustą ofertę
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

    # --- SECURITY CHECK ---
    # Jeśli oferta nie jest w trybie DRAFT i nie jest ODRZUCONA, blokujemy edycję
    # --- POPRAWKA: Pozwalamy edytować też w trakcie konsultacji ---
    if offer.status not in [Offer.Status.DRAFT, Offer.Status.IN_CONSULTATION, Offer.Status.REJECTED]:
        messages.error(request, "Nie można edytować oferty, która została już wysłana lub zatwierdzona.")
        return redirect('offer_detail', pk=pk)
    # ----------------------

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


# --- WIDOK: PDF  ---
@login_required
def offer_pdf(request, pk):
    offer = get_object_or_404(Offer, pk=pk)

    # --- 1. LOGIKA ŚCIEŻEK (Hybrid Pathing) ---
    if not settings.DEBUG:
        # --- PRODUKCJA (PythonAnywhere) ---
        # Tu pliki są zebrane komendą collectstatic w folderze staticfiles
        base_path = settings.STATIC_ROOT
    else:
        # --- LOKALNIE (Docker / Dev) ---
        # Tu pliki leżą w folderze źródłowym aplikacji
        # Budujemy ścieżkę: BASE_DIR / offers / static
        base_path = os.path.join(settings.BASE_DIR, 'offers', 'static')

    # Pełna ścieżka do pliku CSS na dysku
    css_path = os.path.join(base_path, 'offers', 'pdf_style.css')

    # Logika dla Loga (obrazka)
    # offer.seller.logo.path działa poprawnie i lokalnie (Docker) i na produkcji
    if offer.seller.logo:
        logo_url = 'file://' + offer.seller.logo.path
    else:
        logo_url = None

    print(f"PDF GENERATOR: Używam CSS z: {css_path}")

    context = {
        'offer': offer,
        'logo_url': logo_url,
    }
    html_string = render_to_string('offers/offer_pdf.html', context)

    html = HTML(string=html_string, base_url='')

    if os.path.exists(css_path):
        css = CSS(filename=css_path)
        pdf_file = html.write_pdf(stylesheets=[css])
    else:
        print(f"!!! BŁĄD: Brak pliku CSS pod ścieżką: {css_path} !!!")
        pdf_file = html.write_pdf()

    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'filename="Oferta_{offer.offer_number}.pdf"'
    return response


@login_required
def offer_reject(request, pk):
    offer = get_object_or_404(Offer, pk=pk)

    if request.method == 'POST':
        reason = request.POST.get('rejection_reason')
        if reason:
            offer.status = Offer.Status.REJECTED
            offer.rejection_reason = reason
            offer.save()
            messages.warning(request, f"Oferta odrzucona. Powód: {reason}")
            return redirect('offers:offer_list')
        else:
            messages.error(request, "Musisz podać powód odrzucenia!")

    return render(request, 'offers/offer_reject.html', {'offer': offer})


@login_required
def offer_change_status(request, pk, action):
    # 1. Pobieramy konkretną ofertę (pakiet)
    offer = get_object_or_404(Offer, pk=pk)
    user = request.user

    # 2. Logika przejść (State Machine)

    # SCENARIUSZ A: Wysłanie do akceptacji (Draft -> Pending)
    if action == 'submit':
        if offer.status == Offer.Status.DRAFT:
            offer.status = Offer.Status.PENDING
            offer.save()
            messages.success(request, f"Oferta {offer.offer_number} wysłana do akceptacji.")
        else:
            messages.warning(request, "Tylko szkic można wysłać do akceptacji.")

    # SCENARIUSZ B: Zatwierdzenie (Pending -> Approved)
    elif action == 'approve':
        if user.is_superuser:
            if offer.status == Offer.Status.PENDING:
                offer.status = Offer.Status.APPROVED
                offer.save()
                messages.success(request, "Oferta zatwierdzona! Można generować PDF.")
            else:
                messages.warning(request, "Zatwierdzić można tylko oczekującą ofertę.")
        else:
            messages.error(request, "Brak uprawnień (wymagany CEO).")

    # SCENARIUSZ C: Odrzucenie (Pending -> Rejected)

    elif action == 'reject':
        if request.method == 'POST':
            reason = request.POST.get('rejection_reason')
            if reason:
                offer.status = Offer.Status.REJECTED
                offer.rejection_reason = reason
                offer.save()
                messages.warning(request, f"Oferta odrzucona. Powód: {reason}")
                return redirect('offer_list')
            else:
                messages.error(request, "Musisz podać powód odrzucenia!")

        return render(request, 'offers/offer_reject.html', {'offer': offer})


    # SCENARIUSZ D: Cofnięcie do Draftu (np. żeby poprawić odrzuconą)
    elif action == 'draft':
        if offer.status == Offer.Status.REJECTED:
            offer.status = Offer.Status.DRAFT
            offer.save()
            messages.info(request, "Oferta przywrócona do edycji.")

    return redirect('offer_list')

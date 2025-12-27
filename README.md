# 🚀 System Ofertowania B2B (Django CRM)

Kompleksowa aplikacja webowa do zarządzania procesem tworzenia, akceptacji i generowania ofert handlowych. System usprawnia komunikację na linii **Handlowiec ↔ CEO ↔ Dział Techniczny**.



## 📋 O Projekcie

Aplikacja rozwiązuje problem "ręcznego" tworzenia ofert w Excelu i mailowego przesyłania plików. Zapewnia pełną kontrolę nad obiegiem dokumentów, automatyzuje obliczenia matematyczne (VAT/Brutto) i generuje profesjonalne pliki PDF gotowe do wysyłki do klienta.

### Kluczowe Funkcjonalności:

* **Pełny cykl życia oferty:** Od szkicu (`Robocza`), przez weryfikację (`Oczekuje`), aż po finalizację (`Zatwierdzona`) lub odrzucenie.
* **Logika Biznesowa i Matematyka:** Automatyczne przeliczanie kwot Netto, stawek VAT (23%) oraz sum Brutto.
* **Generator PDF:** Tworzenie profesjonalnych dokumentów (faktur pro-forma/ofert) jednym kliknięciem (biblioteka `WeasyPrint`).
* **Moduł Konsultacji:** Możliwość wysłania oferty do weryfikacji technicznej ("Konsultacja z Seniorem") wraz z notatką/pytaniem.
* **System Odrzucania (Feedback):** CEO odrzucając ofertę, musi podać powód decyzji. Handlowiec widzi uzasadnienie, może poprawić ofertę i wysłać ją ponownie.
* **Wizualizacja Statusów:** Kolorystyczne oznaczenia statusów (badge) ułatwiające szybki przegląd sytuacji.
* **Panel Administracyjny:** Pełne zarządzanie słownikami (Klienci, Firmy, Produkty).

## 🛠️ Technologie

Projekt zbudowany w oparciu o nowoczesny stos technologiczny:

* **Backend:** Python 3.11+, Django 5.x
* **Frontend:** HTML5, CSS3, Bootstrap 5 (Responsive Design)
* **Baza danych:** SQLite (Dev) / PostgreSQL (Prod ready)
* **PDF Engine:** WeasyPrint
* **Inne:** Django Crispy Forms, System Powiadomień (Messages Framework)

## 🔄 Workflow (Obieg Dokumentu)

1.  **Handlowiec:** Tworzy ofertę (Status: *Robocza*). Może ją edytować do woli.
2.  **Handlowiec:** Wysyła ofertę do akceptacji (Status: *Oczekuje*) LUB do konsultacji technicznej (Status: *Konsultacja*).
3.  **CEO / Manager:**
    * ✅ **Zatwierdza:** Oferta dostaje status *Zatwierdzona* -> Generowanie PDF możliwe.
    * ❌ **Odrzuca:** Musi wpisać powód odrzucenia. Status zmienia się na *Odrzucona* (czerwony alert).
4.  **Poprawa:** Handlowiec widzi powód odrzucenia, edytuje ofertę (status wraca do *Robocza*) i proces startuje od nowa.



## ⚙️ Instalacja i Uruchomienie

Aby uruchomić projekt lokalnie:

1.  **Sklonuj repozytorium:**
    ```bash
    git clone [https://github.com/twoj-nick/system-ofertowania.git](https://github.com/twoj-nick/system-ofertowania.git)
    cd system-ofertowania
    ```

2.  **Utwórz i aktywuj środowisko wirtualne:**
    ```bash
    python -m venv venv
    # Windows:
    venv\Scripts\activate
    # Mac/Linux:
    source venv/bin/activate
    ```

3.  **Zainstaluj zależności:**
    ```bash
    pip install -r requirements.txt
    ```
    *(Wymagane biblioteki: GTK3 dla WeasyPrint - sprawdź dokumentację, jeśli masz błąd z PDF)*

4.  **Wykonaj migracje bazy danych:**
    ```bash
    python manage.py migrate
    ```

5.  **Utwórz superużytkownika (Admina):**
    ```bash
    python manage.py createsuperuser
    ```

6.  **Uruchom serwer:**
    ```bash
    python manage.py runserver
    ```

## 📝 Do zrobienia (Roadmap)

* [ ] Wysyłanie ofert mailem bezpośrednio z aplikacji.
* [ ] Historia zmian w ofercie (Logi).
* [ ] Dashboard ze statystykami sprzedaży.

---
Autor: **Jcobn3011**

from django.contrib import admin
from django.urls import path, include  # <--- WAŻNE: Dodaj 'include'
from django.conf import settings
from django.conf.urls.static import static
from offers import views as offer_views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # --- TO JEST NOWOŚĆ: Bramka logowania ---
    # To magiczna linijka, która tworzy ścieżki: /accounts/login/, /accounts/logout/ itp.
    path('accounts/', include('django.contrib.auth.urls')),

    path('', offer_views.home, name='home'),
    path('offers/', offer_views.offer_list, name='offer_list'),
    # ... reszta Twoich ścieżek ...
    path('offers/create/', offer_views.offer_create, name='offer_create'),
    path('offers/<int:pk>/', offer_views.offer_detail, name='offer_detail'),
    path('offers/<int:pk>/pdf/', offer_views.offer_pdf, name='offer_pdf'),
    # Dodaj tę linię w urlpatterns:
    path('offers/<int:pk>/edit/', offer_views.offer_edit, name='offer_edit'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
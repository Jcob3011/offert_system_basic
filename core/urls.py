from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from offers import views as offer_views
from offers import views


urlpatterns = [
    path('admin/', admin.site.urls),

    path('accounts/', include('django.contrib.auth.urls')),
    path('', offer_views.home, name='root'),
    path('home/', offer_views.home, name='home'),
    path('offers/', offer_views.offer_list, name='offer_list'),
    path('offers/create/', offer_views.offer_create, name='offer_create'),
    path('offers/<int:pk>/', offer_views.offer_detail, name='offer_detail'),
    path('offers/<int:pk>/pdf/', offer_views.offer_pdf, name='offer_pdf'),
    path('offers/<int:pk>/edit/', offer_views.offer_edit, name='offer_edit'),
    path('offer/<int:pk>/status/<str:action>/', views.offer_change_status, name='offer_change_status'),
    path('offer/<int:pk>/reject/', views.offer_reject, name='offer_reject'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('chpa/', include('chpa_data.urls', namespace='chpa')),
    path('accounts/', include('django.contrib.auth.urls')),
]

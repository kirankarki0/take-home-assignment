"""URL Configuration for backend."""
from django.urls import path, include

urlpatterns = [
    path('api/', include('work_items.urls')),
]

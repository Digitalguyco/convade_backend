from django.urls import path, include
from rest_framework.routers import DefaultRouter

app_name = 'payments'

router = DefaultRouter()

urlpatterns = [
    # Payment endpoints will be added here
    path('', include(router.urls)),
] 
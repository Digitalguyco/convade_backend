from django.urls import path, include
from rest_framework.routers import DefaultRouter

app_name = 'certifications'

router = DefaultRouter()

urlpatterns = [
    # Certification endpoints will be added here
    path('', include(router.urls)),
] 
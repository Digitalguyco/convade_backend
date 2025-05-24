from django.urls import path, include
from rest_framework.routers import DefaultRouter

app_name = 'analytics'

router = DefaultRouter()

urlpatterns = [
    # Analytics endpoints will be added here
    path('', include(router.urls)),
] 
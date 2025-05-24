from django.urls import path, include
from rest_framework.routers import DefaultRouter

app_name = 'notifications'

router = DefaultRouter()

urlpatterns = [
    # Notification endpoints will be added here
    path('', include(router.urls)),
] 
from django.urls import path, include
from rest_framework.routers import DefaultRouter

app_name = 'helpcenter'

router = DefaultRouter()

urlpatterns = [
    # Help center endpoints will be added here
    path('', include(router.urls)),
] 
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'tests'

# Create a router and register our viewsets
router = DefaultRouter()
router.register(r'tests', views.TestViewSet, basename='test')
router.register(r'questions', views.QuestionViewSet, basename='question')
router.register(r'attempts', views.TestAttemptViewSet, basename='attempt')
router.register(r'results', views.TestResultViewSet, basename='result')
router.register(r'question-banks', views.QuestionBankViewSet, basename='questionbank')

# The API URLs are now determined automatically by the router
urlpatterns = [
    path('', include(router.urls)),
] 
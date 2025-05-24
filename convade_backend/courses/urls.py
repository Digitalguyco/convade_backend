from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'courses'

# Create a router and register our viewsets
router = DefaultRouter()
router.register(r'categories', views.CategoryViewSet)
router.register(r'courses', views.CourseViewSet, basename='course')
router.register(r'modules', views.ModuleViewSet, basename='module')
router.register(r'lessons', views.LessonViewSet, basename='lesson')
router.register(r'enrollments', views.EnrollmentViewSet, basename='enrollment')
router.register(r'announcements', views.AnnouncementViewSet, basename='announcement')

# The API URLs are now determined automatically by the router
urlpatterns = [
    path('', include(router.urls)),
] 
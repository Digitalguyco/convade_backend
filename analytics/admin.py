from django.contrib import admin
from .models import (
    UserActivity, CourseAnalytics, TestAnalytics, SystemMetrics,
    UserLearningAnalytics, LearningPath, LearningPathItem
)


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ('user', 'activity_type', 'course')
    list_filter = ('activity_type', 'course')
    search_fields = ('user__email', 'activity_type')


@admin.register(CourseAnalytics)
class CourseAnalyticsAdmin(admin.ModelAdmin):
    list_display = ('course', 'total_enrollments', 'completion_rate')
    search_fields = ('course__title',)


@admin.register(TestAnalytics)
class TestAnalyticsAdmin(admin.ModelAdmin):
    list_display = ('test', 'total_attempts', 'average_score', 'pass_rate')
    search_fields = ('test__title',)


@admin.register(SystemMetrics)
class SystemMetricsAdmin(admin.ModelAdmin):
    list_display = ('__str__',)
    search_fields = ()


@admin.register(UserLearningAnalytics)
class UserLearningAnalyticsAdmin(admin.ModelAdmin):
    list_display = ('user',)
    search_fields = ('user__email',)


@admin.register(LearningPath)
class LearningPathAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'status')
    search_fields = ('name', 'user__email')


@admin.register(LearningPathItem)
class LearningPathItemAdmin(admin.ModelAdmin):
    list_display = ('learning_path', 'order')
    search_fields = ('learning_path__name',)

from django.contrib import admin
from .models import (
    BadgeCategory, Badge, UserBadge, BadgeProgress, Achievement,
    Leaderboard, LeaderboardEntry, UserPoints, PointTransaction
)


@admin.register(BadgeCategory)
class BadgeCategoryAdmin(admin.ModelAdmin):
    """Admin configuration for BadgeCategory model."""
    
    list_display = ('name', 'description', 'badge_count', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'description')
    ordering = ('name',)
    
    def badge_count(self, obj):
        return obj.badges.count()
    badge_count.short_description = 'Badges'


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    """Admin configuration for Badge model."""
    
    list_display = ('name', 'category', 'trigger_type', 'points_value', 'earned_count')
    list_filter = ('category', 'trigger_type', 'course')
    search_fields = ('name', 'description', 'trigger_condition')
    ordering = ('name',)
    
    def earned_count(self, obj):
        return obj.user_badges.count()
    earned_count.short_description = 'Times Earned'


@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    """Admin configuration for UserBadge model."""
    
    list_display = ('user', 'badge', 'earned_at')
    list_filter = ('badge__category', 'earned_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'badge__name')
    ordering = ('-earned_at',)


@admin.register(BadgeProgress)
class BadgeProgressAdmin(admin.ModelAdmin):
    """Admin configuration for BadgeProgress model."""
    
    list_display = ('user', 'badge', 'current_value', 'is_completed')
    list_filter = ('is_completed', 'badge__category')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'badge__name')


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    """Admin configuration for Achievement model."""
    
    list_display = ('title', 'achievement_type')
    list_filter = ('achievement_type',)
    search_fields = ('title', 'description')
    ordering = ('title',)


@admin.register(Leaderboard)
class LeaderboardAdmin(admin.ModelAdmin):
    """Admin configuration for Leaderboard model."""
    
    list_display = ('name', 'leaderboard_type', 'time_period', 'course', 'participant_count')
    list_filter = ('leaderboard_type', 'time_period', 'course')
    search_fields = ('name', 'description', 'course__title')
    
    def participant_count(self, obj):
        return obj.entries.count()
    participant_count.short_description = 'Participants'


@admin.register(LeaderboardEntry)
class LeaderboardEntryAdmin(admin.ModelAdmin):
    """Admin configuration for LeaderboardEntry model."""
    
    list_display = ('leaderboard', 'user', 'rank', 'score')
    list_filter = ('leaderboard', 'rank')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'leaderboard__name')
    ordering = ('leaderboard', 'rank')


@admin.register(UserPoints)
class UserPointsAdmin(admin.ModelAdmin):
    """Admin configuration for UserPoints model."""
    
    list_display = ('user', 'total_points', 'level')
    list_filter = ('level',)
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    ordering = ('-total_points',)


@admin.register(PointTransaction)
class PointTransactionAdmin(admin.ModelAdmin):
    """Admin configuration for PointTransaction model."""
    
    list_display = ('user', 'transaction_type', 'points', 'description_short', 'created_at')
    list_filter = ('transaction_type', 'created_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'description')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    def description_short(self, obj):
        return obj.description[:50] + "..." if len(obj.description) > 50 else obj.description
    description_short.short_description = 'Description'

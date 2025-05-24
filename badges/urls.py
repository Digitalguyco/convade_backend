from django.urls import path, include
from rest_framework.routers import DefaultRouter

app_name = 'badges'

# Router for ViewSets
router = DefaultRouter()
# router.register(r'badges', BadgeViewSet)
# router.register(r'user-badges', UserBadgeViewSet)
# router.register(r'leaderboards', LeaderboardViewSet)

urlpatterns = [
    # Badge management endpoints will be added here
    # path('earned/', EarnedBadgesView.as_view(), name='earned_badges'),
    # path('progress/', BadgeProgressView.as_view(), name='badge_progress'),
    # path('leaderboard/', LeaderboardView.as_view(), name='leaderboard'),
    
    # Include router URLs
    path('', include(router.urls)),
] 
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from accounts.models import User
from courses.models import Course
import uuid


class BadgeCategory(models.Model):
    """Categories for organizing badges."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    icon = models.CharField(max_length=50, blank=True, null=True)
    color = models.CharField(max_length=7, default='#007bff')
    sort_order = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'badges_category'
        verbose_name = 'Badge Category'
        verbose_name_plural = 'Badge Categories'
        ordering = ['sort_order', 'name']
    
    def __str__(self):
        return self.name


class Badge(models.Model):
    """Badge definitions and criteria."""
    
    # Badge types
    ACHIEVEMENT = 'achievement'
    MILESTONE = 'milestone'
    PARTICIPATION = 'participation'
    SKILL = 'skill'
    SPECIAL = 'special'
    
    BADGE_TYPES = [
        (ACHIEVEMENT, 'Achievement'),
        (MILESTONE, 'Milestone'),
        (PARTICIPATION, 'Participation'),
        (SKILL, 'Skill'),
        (SPECIAL, 'Special'),
    ]
    
    # Badge rarity
    COMMON = 'common'
    UNCOMMON = 'uncommon'
    RARE = 'rare'
    EPIC = 'epic'
    LEGENDARY = 'legendary'
    
    RARITY_CHOICES = [
        (COMMON, 'Common'),
        (UNCOMMON, 'Uncommon'),
        (RARE, 'Rare'),
        (EPIC, 'Epic'),
        (LEGENDARY, 'Legendary'),
    ]
    
    # Trigger types
    COURSE_COMPLETION = 'course_completion'
    TEST_SCORE = 'test_score'
    STREAK = 'streak'
    PARTICIPATION_COUNT = 'participation_count'
    TIME_SPENT = 'time_spent'
    PERFECT_SCORE = 'perfect_score'
    FIRST_ATTEMPT = 'first_attempt'
    IMPROVEMENT = 'improvement'
    CUSTOM = 'custom'
    
    TRIGGER_TYPES = [
        (COURSE_COMPLETION, 'Course Completion'),
        (TEST_SCORE, 'Test Score'),
        (STREAK, 'Learning Streak'),
        (PARTICIPATION_COUNT, 'Participation Count'),
        (TIME_SPENT, 'Time Spent Learning'),
        (PERFECT_SCORE, 'Perfect Score'),
        (FIRST_ATTEMPT, 'First Attempt Success'),
        (IMPROVEMENT, 'Score Improvement'),
        (CUSTOM, 'Custom Criteria'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField()
    
    # Badge metadata
    category = models.ForeignKey(BadgeCategory, on_delete=models.CASCADE, related_name='badges')
    badge_type = models.CharField(max_length=20, choices=BADGE_TYPES, default=ACHIEVEMENT)
    rarity = models.CharField(max_length=20, choices=RARITY_CHOICES, default=COMMON)
    
    # Visual elements
    icon = models.ImageField(upload_to='badges/icons/%Y/%m/', blank=True, null=True)
    icon_class = models.CharField(max_length=50, blank=True, null=True)  # CSS icon class
    color = models.CharField(max_length=7, default='#007bff')
    background_color = models.CharField(max_length=7, default='#ffffff')
    
    # Criteria and triggers
    trigger_type = models.CharField(max_length=30, choices=TRIGGER_TYPES, default=COURSE_COMPLETION)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, blank=True, null=True, related_name='badges')
    
    # Numeric criteria
    required_value = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00,
        help_text="Required value for trigger (score, count, etc.)"
    )
    comparison_operator = models.CharField(
        max_length=10,
        choices=[
            ('gte', 'Greater than or equal'),
            ('gt', 'Greater than'),
            ('eq', 'Equal to'),
            ('lt', 'Less than'),
            ('lte', 'Less than or equal'),
        ],
        default='gte'
    )
    
    # Advanced criteria
    criteria_json = models.JSONField(
        default=dict, 
        blank=True,
        help_text="Additional criteria in JSON format"
    )
    
    # Badge settings
    is_active = models.BooleanField(default=True)
    is_stackable = models.BooleanField(default=False)  # Can be earned multiple times
    max_awards = models.PositiveIntegerField(
        default=1,
        help_text="Maximum times this badge can be awarded (0 for unlimited)"
    )
    
    # Points and rewards
    points_value = models.PositiveIntegerField(default=10)
    xp_reward = models.PositiveIntegerField(default=0)
    
    # Visibility and availability
    is_secret = models.BooleanField(default=False)  # Hidden until earned
    available_from = models.DateTimeField(blank=True, null=True)
    available_until = models.DateTimeField(blank=True, null=True)
    
    # Prerequisites
    prerequisite_badges = models.ManyToManyField(
        'self', 
        blank=True, 
        symmetrical=False,
        related_name='unlocks_badges'
    )
    
    # Analytics
    total_awarded = models.PositiveIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_badges')
    
    class Meta:
        db_table = 'badges_badge'
        verbose_name = 'Badge'
        verbose_name_plural = 'Badges'
        ordering = ['category', 'name']
        indexes = [
            models.Index(fields=['trigger_type']),
            models.Index(fields=['course']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_rarity_display()})"
    
    @property
    def is_available(self):
        """Check if badge is currently available."""
        now = timezone.now()
        if self.available_from and now < self.available_from:
            return False
        if self.available_until and now > self.available_until:
            return False
        return self.is_active
    
    def check_criteria(self, user, context=None):
        """Check if user meets the criteria for this badge."""
        if not self.is_available:
            return False
        
        # Check prerequisites
        if self.prerequisite_badges.exists():
            user_badges = UserBadge.objects.filter(
                user=user, 
                badge__in=self.prerequisite_badges.all()
            ).values_list('badge_id', flat=True)
            
            if not set(self.prerequisite_badges.values_list('id', flat=True)).issubset(set(user_badges)):
                return False
        
        # Check if already awarded and not stackable
        if not self.is_stackable:
            if UserBadge.objects.filter(user=user, badge=self).exists():
                return False
        
        # Check max awards
        if self.max_awards > 0:
            current_awards = UserBadge.objects.filter(user=user, badge=self).count()
            if current_awards >= self.max_awards:
                return False
        
        # Check specific criteria based on trigger type
        return self._check_trigger_criteria(user, context)
    
    def _check_trigger_criteria(self, user, context):
        """Check trigger-specific criteria."""
        from courses.models import Enrollment
        from tests.models import TestResult
        
        if self.trigger_type == self.COURSE_COMPLETION:
            if self.course:
                enrollment = Enrollment.objects.filter(
                    student=user, 
                    course=self.course, 
                    status=Enrollment.COMPLETED
                ).first()
                return enrollment is not None
            else:
                # Any course completion
                completed_courses = Enrollment.objects.filter(
                    student=user, 
                    status=Enrollment.COMPLETED
                ).count()
                return self._compare_value(completed_courses, self.required_value)
        
        elif self.trigger_type == self.TEST_SCORE:
            if context and 'test_result' in context:
                test_result = context['test_result']
                return self._compare_value(test_result.best_percentage, self.required_value)
        
        elif self.trigger_type == self.PERFECT_SCORE:
            if context and 'test_result' in context:
                test_result = context['test_result']
                return test_result.best_percentage == 100
        
        # Add more trigger type checks here
        
        return False
    
    def _compare_value(self, actual_value, required_value):
        """Compare values based on comparison operator."""
        if self.comparison_operator == 'gte':
            return actual_value >= required_value
        elif self.comparison_operator == 'gt':
            return actual_value > required_value
        elif self.comparison_operator == 'eq':
            return actual_value == required_value
        elif self.comparison_operator == 'lt':
            return actual_value < required_value
        elif self.comparison_operator == 'lte':
            return actual_value <= required_value
        return False


class UserBadge(models.Model):
    """Badges earned by users."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='earned_badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE, related_name='user_badges')
    
    # Award details
    earned_at = models.DateTimeField(auto_now_add=True)
    awarded_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        blank=True, 
        null=True,
        related_name='awarded_badges'
    )
    
    # Context when earned
    trigger_context = models.JSONField(
        default=dict, 
        blank=True,
        help_text="Context data when badge was earned"
    )
    
    # Progress tracking (for stackable badges)
    progress_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Visibility
    is_featured = models.BooleanField(default=False)  # Show prominently on profile
    is_public = models.BooleanField(default=True)  # Visible to others
    
    # Notifications
    notification_sent = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'badges_user_badge'
        verbose_name = 'User Badge'
        verbose_name_plural = 'User Badges'
        ordering = ['-earned_at']
        indexes = [
            models.Index(fields=['user', 'earned_at']),
            models.Index(fields=['badge']),
        ]
    
    def __str__(self):
        return f"{self.user.full_name} - {self.badge.name}"


class BadgeProgress(models.Model):
    """Track user progress towards earning badges."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='badge_progress')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE, related_name='user_progress')
    
    # Progress tracking
    current_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    required_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    progress_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Status
    is_completed = models.BooleanField(default=False)
    is_eligible = models.BooleanField(default=True)  # Meets prerequisites
    
    # Tracking
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'badges_badge_progress'
        verbose_name = 'Badge Progress'
        verbose_name_plural = 'Badge Progress'
        unique_together = ['user', 'badge']
        ordering = ['-progress_percentage', '-last_updated']
        indexes = [
            models.Index(fields=['user', 'is_completed']),
            models.Index(fields=['badge']),
        ]
    
    def __str__(self):
        return f"{self.user.full_name} - {self.badge.name} ({self.progress_percentage}%)"
    
    def update_progress(self, new_value):
        """Update progress value and percentage."""
        self.current_value = new_value
        if self.required_value > 0:
            self.progress_percentage = min(100, (new_value / self.required_value) * 100)
        
        if self.progress_percentage >= 100 and not self.is_completed:
            self.is_completed = True
            # Trigger badge award if criteria met
            if self.badge.check_criteria(self.user):
                self._award_badge()
        
        self.save()
    
    def _award_badge(self):
        """Award the badge to the user."""
        UserBadge.objects.create(
            user=self.user,
            badge=self.badge,
            progress_value=self.current_value
        )
        
        # Update badge statistics
        self.badge.total_awarded += 1
        self.badge.save(update_fields=['total_awarded'])


class Achievement(models.Model):
    """Custom achievements and milestones."""
    
    # Achievement types
    LEARNING_STREAK = 'learning_streak'
    COURSE_MASTER = 'course_master'
    TEST_CHAMPION = 'test_champion'
    EARLY_BIRD = 'early_bird'
    NIGHT_OWL = 'night_owl'
    PERFECTIONIST = 'perfectionist'
    IMPROVER = 'improver'
    SOCIAL_LEARNER = 'social_learner'
    
    ACHIEVEMENT_TYPES = [
        (LEARNING_STREAK, 'Learning Streak'),
        (COURSE_MASTER, 'Course Master'),
        (TEST_CHAMPION, 'Test Champion'),
        (EARLY_BIRD, 'Early Bird'),
        (NIGHT_OWL, 'Night Owl'),
        (PERFECTIONIST, 'Perfectionist'),
        (IMPROVER, 'Improver'),
        (SOCIAL_LEARNER, 'Social Learner'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='achievements')
    achievement_type = models.CharField(max_length=30, choices=ACHIEVEMENT_TYPES)
    
    # Achievement data
    title = models.CharField(max_length=200)
    description = models.TextField()
    value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Context
    course = models.ForeignKey(Course, on_delete=models.CASCADE, blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    achieved_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'badges_achievement'
        verbose_name = 'Achievement'
        verbose_name_plural = 'Achievements'
        ordering = ['-achieved_at']
        indexes = [
            models.Index(fields=['user', 'achievement_type']),
            models.Index(fields=['achieved_at']),
        ]
    
    def __str__(self):
        return f"{self.user.full_name} - {self.title}"


class Leaderboard(models.Model):
    """Leaderboard configurations and rankings."""
    
    # Leaderboard types
    POINTS = 'points'
    BADGES = 'badges'
    COURSE_COMPLETION = 'course_completion'
    TEST_SCORES = 'test_scores'
    STREAK = 'streak'
    TIME_SPENT = 'time_spent'
    
    LEADERBOARD_TYPES = [
        (POINTS, 'Points'),
        (BADGES, 'Badges'),
        (COURSE_COMPLETION, 'Course Completion'),
        (TEST_SCORES, 'Test Scores'),
        (STREAK, 'Learning Streak'),
        (TIME_SPENT, 'Time Spent'),
    ]
    
    # Time periods
    ALL_TIME = 'all_time'
    YEARLY = 'yearly'
    MONTHLY = 'monthly'
    WEEKLY = 'weekly'
    DAILY = 'daily'
    
    TIME_PERIODS = [
        (ALL_TIME, 'All Time'),
        (YEARLY, 'Yearly'),
        (MONTHLY, 'Monthly'),
        (WEEKLY, 'Weekly'),
        (DAILY, 'Daily'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    
    # Configuration
    leaderboard_type = models.CharField(max_length=30, choices=LEADERBOARD_TYPES, default=POINTS)
    time_period = models.CharField(max_length=20, choices=TIME_PERIODS, default=ALL_TIME)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, blank=True, null=True)
    
    # Settings
    is_active = models.BooleanField(default=True)
    is_public = models.BooleanField(default=True)
    max_entries = models.PositiveIntegerField(default=100)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'badges_leaderboard'
        verbose_name = 'Leaderboard'
        verbose_name_plural = 'Leaderboards'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_time_period_display()})"


class LeaderboardEntry(models.Model):
    """Individual leaderboard entries."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    leaderboard = models.ForeignKey(Leaderboard, on_delete=models.CASCADE, related_name='entries')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='leaderboard_entries')
    
    # Ranking data
    rank = models.PositiveIntegerField()
    score = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    
    # Additional data
    metadata = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'badges_leaderboard_entry'
        verbose_name = 'Leaderboard Entry'
        verbose_name_plural = 'Leaderboard Entries'
        unique_together = ['leaderboard', 'user', 'period_start']
        ordering = ['leaderboard', 'rank']
        indexes = [
            models.Index(fields=['leaderboard', 'rank']),
            models.Index(fields=['user']),
        ]
    
    def __str__(self):
        return f"{self.leaderboard.name} - #{self.rank} {self.user.full_name}"


class UserPoints(models.Model):
    """Track user points and XP."""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='points')
    
    # Points
    total_points = models.PositiveIntegerField(default=0)
    available_points = models.PositiveIntegerField(default=0)  # Points that can be spent
    spent_points = models.PositiveIntegerField(default=0)
    
    # Experience
    total_xp = models.PositiveIntegerField(default=0)
    level = models.PositiveIntegerField(default=1)
    xp_to_next_level = models.PositiveIntegerField(default=100)
    
    # Streaks
    current_streak = models.PositiveIntegerField(default=0)
    longest_streak = models.PositiveIntegerField(default=0)
    last_activity_date = models.DateField(blank=True, null=True)
    
    # Statistics
    badges_earned = models.PositiveIntegerField(default=0)
    courses_completed = models.PositiveIntegerField(default=0)
    tests_passed = models.PositiveIntegerField(default=0)
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'badges_user_points'
        verbose_name = 'User Points'
        verbose_name_plural = 'User Points'
    
    def __str__(self):
        return f"{self.user.full_name} - Level {self.level} ({self.total_points} points)"
    
    def add_points(self, points, reason=""):
        """Add points to user account."""
        self.total_points += points
        self.available_points += points
        self._check_level_up()
        self.save()
        
        # Log the transaction
        PointTransaction.objects.create(
            user=self.user,
            points=points,
            transaction_type=PointTransaction.EARNED,
            reason=reason
        )
    
    def spend_points(self, points, reason=""):
        """Spend user points."""
        if self.available_points >= points:
            self.available_points -= points
            self.spent_points += points
            self.save()
            
            # Log the transaction
            PointTransaction.objects.create(
                user=self.user,
                points=-points,
                transaction_type=PointTransaction.SPENT,
                reason=reason
            )
            return True
        return False
    
    def add_xp(self, xp):
        """Add XP and check for level up."""
        self.total_xp += xp
        self._check_level_up()
        self.save()
    
    def _check_level_up(self):
        """Check if user should level up."""
        # Simple level calculation: level = sqrt(total_xp / 100)
        import math
        new_level = max(1, int(math.sqrt(self.total_xp / 100)) + 1)
        
        if new_level > self.level:
            self.level = new_level
            # Award level up points
            self.add_points(new_level * 10, f"Level {new_level} reached")
        
        # Calculate XP needed for next level
        next_level_xp = ((self.level) ** 2) * 100
        self.xp_to_next_level = max(0, next_level_xp - self.total_xp)


class PointTransaction(models.Model):
    """Track point transactions."""
    
    EARNED = 'earned'
    SPENT = 'spent'
    BONUS = 'bonus'
    PENALTY = 'penalty'
    
    TRANSACTION_TYPES = [
        (EARNED, 'Earned'),
        (SPENT, 'Spent'),
        (BONUS, 'Bonus'),
        (PENALTY, 'Penalty'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='point_transactions')
    points = models.IntegerField()  # Can be negative for spending
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    reason = models.CharField(max_length=200)
    
    # Context
    badge = models.ForeignKey(Badge, on_delete=models.SET_NULL, blank=True, null=True)
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'badges_point_transaction'
        verbose_name = 'Point Transaction'
        verbose_name_plural = 'Point Transactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.full_name} - {self.points} points ({self.reason})"

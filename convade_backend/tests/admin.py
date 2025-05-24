from django.contrib import admin
from django.utils.html import format_html
from .models import (
    QuestionBank, BankQuestion, BankAnswer, Test, Question, Answer, 
    TestAttempt, QuestionResponse, TestResult
)


@admin.register(QuestionBank)
class QuestionBankAdmin(admin.ModelAdmin):
    """Admin configuration for QuestionBank model."""
    
    list_display = ('name', 'description', 'question_count', 'is_public', 'created_at')
    list_filter = ('is_public', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('name',)
    
    def question_count(self, obj):
        return obj.questions.count()
    question_count.short_description = 'Questions'


@admin.register(BankQuestion)
class BankQuestionAdmin(admin.ModelAdmin):
    """Admin configuration for BankQuestion model."""
    
    list_display = (
        'question_text_short', 'bank', 'question_type', 'difficulty', 
        'points', 'created_at'
    )
    list_filter = ('question_type', 'difficulty', 'bank')
    search_fields = ('question_text', 'explanation', 'tags')
    ordering = ('-created_at',)
    
    fieldsets = (
        (None, {'fields': ('bank', 'question_text', 'question_type')}),
        ('Settings', {'fields': ('difficulty', 'points')}),
        ('Media', {'fields': ('image',)}),
        ('Additional Info', {'fields': ('explanation', 'tags')}),
    )
    
    def question_text_short(self, obj):
        return obj.question_text[:50] + "..." if len(obj.question_text) > 50 else obj.question_text
    question_text_short.short_description = 'Question'


@admin.register(BankAnswer)
class BankAnswerAdmin(admin.ModelAdmin):
    """Admin configuration for BankAnswer model."""
    
    list_display = ('answer_text_short', 'question', 'is_correct', 'order')
    list_filter = ('is_correct',)
    search_fields = ('answer_text', 'question__question_text')
    ordering = ('question', 'order')
    
    def answer_text_short(self, obj):
        return obj.answer_text[:30] + "..." if len(obj.answer_text) > 30 else obj.answer_text
    answer_text_short.short_description = 'Answer'


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    """Admin configuration for Test model."""
    
    list_display = (
        'title', 'course', 'instructor', 'test_type', 'status', 
        'total_points', 'time_limit', 'attempt_count', 'available_from'
    )
    list_filter = ('test_type', 'status', 'course__category', 'available_from')
    search_fields = ('title', 'description', 'course__title', 'instructor__email')
    ordering = ('-created_at',)
    date_hierarchy = 'available_from'
    
    fieldsets = (
        (None, {'fields': ('title', 'description', 'course', 'instructor')}),
        ('Test Settings', {
            'fields': (
                'test_type', 'total_points', 'passing_score', 'time_limit',
                'max_attempts', 'allow_review', 'randomize_questions'
            )
        }),
        ('Availability', {
            'fields': ('available_from', 'available_until', 'status')
        }),
        ('Proctoring', {
            'fields': (
                'require_webcam', 'prevent_copy_paste', 'full_screen_mode'
            ),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def attempt_count(self, obj):
        return obj.attempts.count()
    attempt_count.short_description = 'Attempts'


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    """Admin configuration for Question model."""
    
    list_display = (
        'question_text_short', 'test', 'question_type', 'points', 
        'order', 'is_required'
    )
    list_filter = ('question_type', 'is_required', 'test__course')
    search_fields = ('question_text', 'test__title')
    ordering = ('test', 'order')
    
    fieldsets = (
        (None, {'fields': ('test', 'question_text', 'question_type', 'order')}),
        ('Settings', {'fields': ('points', 'is_required')}),
        ('Media', {'fields': ('image',)}),
        ('Additional Info', {'fields': ('explanation',)}),
    )
    
    def question_text_short(self, obj):
        return obj.question_text[:50] + "..." if len(obj.question_text) > 50 else obj.question_text
    question_text_short.short_description = 'Question'


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    """Admin configuration for Answer model."""
    
    list_display = ('answer_text_short', 'question', 'is_correct', 'order')
    list_filter = ('is_correct', 'question__test')
    search_fields = ('answer_text', 'question__question_text')
    ordering = ('question', 'order')
    
    def answer_text_short(self, obj):
        return obj.answer_text[:30] + "..." if len(obj.answer_text) > 30 else obj.answer_text
    answer_text_short.short_description = 'Answer'


@admin.register(TestAttempt)
class TestAttemptAdmin(admin.ModelAdmin):
    """Admin configuration for TestAttempt model."""
    
    list_display = (
        'test', 'student', 'attempt_number', 'status', 'score', 
        'is_passed', 'started_at', 'submitted_at'
    )
    list_filter = ('status', 'is_passed', 'test__course', 'started_at')
    search_fields = (
        'student__email', 'student__first_name', 'student__last_name',
        'test__title'
    )
    ordering = ('-started_at',)
    date_hierarchy = 'started_at'
    
    readonly_fields = (
        'started_at', 'submitted_at', 'time_spent', 'ip_address',
        'user_agent'
    )
    
    fieldsets = (
        (None, {'fields': ('test', 'student', 'attempt_number')}),
        ('Results', {'fields': ('status', 'score', 'percentage', 'is_passed')}),
        ('Timing', {'fields': ('started_at', 'submitted_at', 'time_spent')}),
        ('Proctoring Data', {
            'fields': ('ip_address', 'user_agent', 'browser_events'),
            'classes': ('collapse',)
        }),
    )


@admin.register(QuestionResponse)
class QuestionResponseAdmin(admin.ModelAdmin):
    """Admin configuration for QuestionResponse model."""
    
    list_display = (
        'attempt', 'question', 'is_correct', 
        'points_earned', 'created_at'
    )
    list_filter = ('is_correct', 'question__question_type', 'created_at')
    search_fields = (
        'attempt__student__email', 'question__question_text'
    )
    ordering = ('-created_at',)
    
    readonly_fields = ('created_at', 'time_spent')


@admin.register(TestResult)
class TestResultAdmin(admin.ModelAdmin):
    """Admin configuration for TestResult model."""
    
    list_display = (
        'test', 'student', 'best_score', 'best_percentage', 
        'is_passed', 'total_attempts', 'updated_at'
    )
    list_filter = ('is_passed', 'test__course', 'updated_at')
    search_fields = (
        'student__email', 'student__first_name', 'student__last_name',
        'test__title'
    )
    ordering = ('-updated_at',)
    date_hierarchy = 'updated_at'
    
    readonly_fields = ('updated_at',)

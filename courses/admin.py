from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Course, Module, Lesson, Enrollment, LessonProgress, Announcement


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Admin configuration for Category model."""
    
    list_display = ('name', 'slug', 'description', 'is_active', 'course_count', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('name',)
    
    def course_count(self, obj):
        return obj.courses.count()
    course_count.short_description = 'Courses'


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    """Admin configuration for Course model."""
    
    list_display = (
        'title', 'course_code', 'instructor', 'category', 'status', 
        'enrollment_count', 'price', 'published_at'
    )
    list_filter = ('status', 'category', 'difficulty', 'published_at')
    search_fields = ('title', 'course_code', 'description', 'instructor__email')
    ordering = ('-created_at',)
    date_hierarchy = 'published_at'
    
    fieldsets = (
        (None, {'fields': ('title', 'course_code', 'description')}),
        ('Course Details', {
            'fields': (
                'instructor', 'category', 'difficulty', 
                'estimated_duration'
            )
        }),
        ('Media', {'fields': ('thumbnail',)}),
        ('Pricing', {'fields': ('price', 'is_free')}),
        ('Enrollment', {
            'fields': (
                'max_students', 'enrollment_start', 'enrollment_end',
                'prerequisites'
            )
        }),
        ('Status', {'fields': ('status',)}),
        ('Publishing', {'fields': ('published_at',)}),
    )
    
    filter_horizontal = ('prerequisites',)
    readonly_fields = ('created_at', 'updated_at')
    
    def enrollment_count(self, obj):
        return obj.enrollments.filter(status='active').count()
    enrollment_count.short_description = 'Enrollments'


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    """Admin configuration for Module model."""
    
    list_display = ('title', 'course', 'order', 'lesson_count', 'is_published', 'created_at')
    list_filter = ('is_published', 'course__category', 'created_at')
    search_fields = ('title', 'description', 'course__title')
    ordering = ('course', 'order')
    
    def lesson_count(self, obj):
        return obj.lessons.count()
    lesson_count.short_description = 'Lessons'


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    """Admin configuration for Lesson model."""
    
    list_display = (
        'title', 'module', 'lesson_type', 'order', 
        'duration', 'is_published', 'created_at'
    )
    list_filter = ('lesson_type', 'is_published', 'module__course', 'created_at')
    search_fields = ('title', 'content', 'module__title')
    ordering = ('module', 'order')
    
    fieldsets = (
        (None, {'fields': ('title', 'module', 'order')}),
        ('Content', {'fields': ('lesson_type', 'content', 'video_url', 'attachment')}),
        ('Settings', {'fields': ('duration', 'is_published')}),
    )


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    """Admin configuration for Enrollment model."""
    
    list_display = (
        'student', 'course', 'status', 'progress_percentage', 
        'enrollment_date', 'completion_date'
    )
    list_filter = ('status', 'course__category', 'enrollment_date')
    search_fields = (
        'student__email', 'student__first_name', 'student__last_name', 
        'course__title'
    )
    ordering = ('-enrollment_date',)
    date_hierarchy = 'enrollment_date'
    
    readonly_fields = ('enrollment_date', 'completion_date', 'progress_percentage')


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    """Admin configuration for LessonProgress model."""
    
    list_display = (
        'enrollment', 'lesson', 'status', 'completion_percentage', 
        'started_at', 'completed_at'
    )
    list_filter = ('status', 'lesson__lesson_type', 'completed_at')
    search_fields = (
        'enrollment__student__email', 'lesson__title'
    )
    ordering = ('-started_at',)
    
    readonly_fields = ('started_at', 'completed_at')


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    """Admin configuration for Announcement model."""
    
    list_display = (
        'title', 'course', 'instructor', 'is_urgent', 
        'is_published', 'created_at'
    )
    list_filter = ('is_urgent', 'is_published', 'course', 'created_at')
    search_fields = ('title', 'content', 'course__title')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (None, {'fields': ('title', 'content', 'course', 'instructor')}),
        ('Publishing', {'fields': ('is_urgent', 'is_published')}),
    )
    
    readonly_fields = ('created_at', 'updated_at')

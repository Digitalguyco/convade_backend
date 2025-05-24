from rest_framework import serializers
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema_field
from .models import (
    Category, Course, Module, Lesson, Enrollment, 
    LessonProgress, Announcement
)

User = get_user_model()


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for course categories."""
    
    course_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'slug', 'description', 'icon', 'color',
            'is_active', 'sort_order', 'course_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'course_count']
    
    @extend_schema_field(serializers.IntegerField)
    def get_course_count(self, obj):
        return obj.courses.filter(status=Course.PUBLISHED).count()


class InstructorSerializer(serializers.ModelSerializer):
    """Basic instructor information serializer."""
    
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email', 'profile_picture']
        read_only_fields = ['id', 'email']


class LessonListSerializer(serializers.ModelSerializer):
    """Serializer for lesson list view."""
    
    class Meta:
        model = Lesson
        fields = [
            'id', 'title', 'lesson_type', 'order', 'is_published',
            'is_free_preview', 'duration', 'view_count'
        ]
        read_only_fields = ['id', 'view_count']


class LessonDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for individual lessons."""
    
    class Meta:
        model = Lesson
        fields = [
            'id', 'module', 'title', 'lesson_type', 'content', 'video_file',
            'video_url', 'attachment', 'order', 'is_published', 'is_free_preview',
            'duration', 'live_session_date', 'live_session_url', 'view_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'view_count', 'created_at', 'updated_at']


class ModuleListSerializer(serializers.ModelSerializer):
    """Serializer for module list view."""
    
    lesson_count = serializers.SerializerMethodField()
    total_duration = serializers.SerializerMethodField()
    
    class Meta:
        model = Module
        fields = [
            'id', 'title', 'description', 'order', 'is_published',
            'estimated_duration', 'lesson_count', 'total_duration'
        ]
        read_only_fields = ['id', 'lesson_count', 'total_duration']
    
    @extend_schema_field(serializers.IntegerField)
    def get_lesson_count(self, obj):
        return obj.lessons.filter(is_published=True).count()
    
    @extend_schema_field(serializers.IntegerField)
    def get_total_duration(self, obj):
        return sum(lesson.duration for lesson in obj.lessons.filter(is_published=True))


class ModuleDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for modules with lessons."""
    
    lessons = LessonListSerializer(many=True, read_only=True)
    lesson_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Module
        fields = [
            'id', 'course', 'title', 'description', 'order', 'is_published',
            'estimated_duration', 'unlock_after', 'lessons', 'lesson_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'lesson_count', 'created_at', 'updated_at']
    
    @extend_schema_field(serializers.IntegerField)
    def get_lesson_count(self, obj):
        return obj.lessons.filter(is_published=True).count()


class CourseListSerializer(serializers.ModelSerializer):
    """Serializer for course list view."""
    
    category = CategorySerializer(read_only=True)
    instructor = InstructorSerializer(read_only=True)
    module_count = serializers.SerializerMethodField()
    completion_rate = serializers.SerializerMethodField()
    is_enrollment_open = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()
    
    class Meta:
        model = Course
        fields = [
            'id', 'title', 'slug', 'short_description', 'course_code',
            'category', 'instructor', 'thumbnail', 'status', 'difficulty',
            'is_free', 'price', 'estimated_duration', 'max_students',
            'enrollment_count', 'completion_rate', 'module_count',
            'is_enrollment_open', 'is_active', 'created_at'
        ]
        read_only_fields = [
            'id', 'enrollment_count', 'completion_rate', 'module_count',
            'is_enrollment_open', 'is_active', 'created_at'
        ]
    
    @extend_schema_field(serializers.IntegerField)
    def get_module_count(self, obj):
        return obj.modules.filter(is_published=True).count()
    
    @extend_schema_field(serializers.FloatField)
    def get_completion_rate(self, obj):
        return obj.completion_rate
    
    @extend_schema_field(serializers.BooleanField)
    def get_is_enrollment_open(self, obj):
        return obj.is_enrollment_open
    
    @extend_schema_field(serializers.BooleanField)
    def get_is_active(self, obj):
        return obj.is_active


class CourseDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for individual courses."""
    
    category = CategorySerializer(read_only=True)
    instructor = InstructorSerializer(read_only=True)
    modules = ModuleListSerializer(many=True, read_only=True)
    prerequisites = CourseListSerializer(many=True, read_only=True)
    is_enrollment_open = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()
    available_slots = serializers.SerializerMethodField()
    completion_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = Course
        fields = [
            'id', 'title', 'slug', 'description', 'short_description',
            'course_code', 'category', 'instructor', 'school', 'thumbnail',
            'intro_video', 'syllabus', 'status', 'difficulty', 'is_free',
            'price', 'estimated_duration', 'start_date', 'end_date',
            'enrollment_start', 'enrollment_end', 'max_students',
            'allow_self_enrollment', 'requires_approval', 'prerequisites',
            'required_materials', 'learning_objectives', 'passing_score',
            'certificate_enabled', 'meta_keywords', 'meta_description',
            'view_count', 'enrollment_count', 'completion_count',
            'modules', 'is_enrollment_open', 'is_active', 'available_slots',
            'completion_rate', 'created_at', 'updated_at', 'published_at'
        ]
        read_only_fields = [
            'id', 'view_count', 'enrollment_count', 'completion_count',
            'is_enrollment_open', 'is_active', 'available_slots',
            'completion_rate', 'created_at', 'updated_at', 'published_at'
        ]
    
    @extend_schema_field(serializers.BooleanField)
    def get_is_enrollment_open(self, obj):
        return obj.is_enrollment_open
    
    @extend_schema_field(serializers.BooleanField)
    def get_is_active(self, obj):
        return obj.is_active
    
    @extend_schema_field(serializers.IntegerField)
    def get_available_slots(self, obj):
        return obj.available_slots
    
    @extend_schema_field(serializers.FloatField)
    def get_completion_rate(self, obj):
        return obj.completion_rate


class CourseCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating courses."""
    
    class Meta:
        model = Course
        fields = [
            'title', 'slug', 'description', 'short_description', 'course_code',
            'category', 'thumbnail', 'intro_video', 'syllabus', 'status',
            'difficulty', 'is_free', 'price', 'estimated_duration',
            'start_date', 'end_date', 'enrollment_start', 'enrollment_end',
            'max_students', 'allow_self_enrollment', 'requires_approval',
            'prerequisites', 'required_materials', 'learning_objectives',
            'passing_score', 'certificate_enabled', 'meta_keywords',
            'meta_description'
        ]
    
    def create(self, validated_data):
        # Set instructor and school from request user
        request = self.context.get('request')
        if request and request.user:
            validated_data['instructor'] = request.user
            validated_data['school'] = request.user.school
        return super().create(validated_data)


class EnrollmentSerializer(serializers.ModelSerializer):
    """Serializer for course enrollments."""
    
    student = InstructorSerializer(read_only=True)
    course = CourseListSerializer(read_only=True)
    is_passed = serializers.SerializerMethodField()
    
    class Meta:
        model = Enrollment
        fields = [
            'id', 'student', 'course', 'status', 'enrollment_date',
            'completion_date', 'progress_percentage', 'last_accessed',
            'current_grade', 'final_grade', 'total_study_time',
            'certificate_issued', 'certificate_date', 'payment_completed',
            'payment_date', 'is_passed'
        ]
        read_only_fields = [
            'id', 'enrollment_date', 'completion_date', 'last_accessed',
            'current_grade', 'final_grade', 'total_study_time',
            'certificate_issued', 'certificate_date', 'is_passed'
        ]
    
    @extend_schema_field(serializers.BooleanField)
    def get_is_passed(self, obj):
        return obj.is_passed


class LessonProgressSerializer(serializers.ModelSerializer):
    """Serializer for lesson progress tracking."""
    
    lesson = LessonListSerializer(read_only=True)
    
    class Meta:
        model = LessonProgress
        fields = [
            'id', 'enrollment', 'lesson', 'status', 'started_at',
            'completed_at', 'last_accessed', 'watch_time',
            'completion_percentage', 'notes', 'is_bookmarked'
        ]
        read_only_fields = ['id', 'started_at', 'completed_at', 'last_accessed']


class AnnouncementSerializer(serializers.ModelSerializer):
    """Serializer for course announcements."""
    
    instructor = InstructorSerializer(read_only=True)
    
    class Meta:
        model = Announcement
        fields = [
            'id', 'course', 'instructor', 'title', 'content', 'is_urgent',
            'is_published', 'send_email', 'target_all_students',
            'target_students', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'instructor', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        # Set instructor from request user
        request = self.context.get('request')
        if request and request.user:
            validated_data['instructor'] = request.user
        return super().create(validated_data) 
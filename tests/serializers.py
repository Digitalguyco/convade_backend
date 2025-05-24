from rest_framework import serializers
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema_field
from typing import List
from .models import (
    Test, Question, Answer, TestAttempt, QuestionResponse, 
    TestResult, QuestionBank, BankQuestion, BankAnswer
)
from courses.models import Course, Lesson

User = get_user_model()


class AnswerSerializer(serializers.ModelSerializer):
    """Serializer for question answers."""
    
    class Meta:
        model = Answer
        fields = [
            'id', 'answer_text', 'is_correct', 'order', 'points', 'match_text'
        ]
        read_only_fields = ['id']


class QuestionListSerializer(serializers.ModelSerializer):
    """Serializer for question list view."""
    
    answer_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Question
        fields = [
            'id', 'question_text', 'question_type', 'order', 'points',
            'is_required', 'difficulty', 'answer_count'
        ]
        read_only_fields = ['id', 'answer_count']
    
    @extend_schema_field(serializers.IntegerField)
    def get_answer_count(self, obj):
        return obj.answers.count()


class QuestionDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for questions with answers."""
    
    answers = AnswerSerializer(many=True, read_only=True)
    
    class Meta:
        model = Question
        fields = [
            'id', 'test', 'question_text', 'question_type', 'order', 'points',
            'is_required', 'image', 'explanation', 'case_sensitive',
            'partial_credit', 'difficulty', 'tags', 'answers',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class QuestionCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating questions."""
    
    answers = AnswerSerializer(many=True, required=False)
    
    class Meta:
        model = Question
        fields = [
            'test', 'question_text', 'question_type', 'order', 'points',
            'is_required', 'image', 'explanation', 'case_sensitive',
            'partial_credit', 'difficulty', 'tags', 'answers'
        ]
    
    def create(self, validated_data):
        answers_data = validated_data.pop('answers', [])
        question = Question.objects.create(**validated_data)
        
        for answer_data in answers_data:
            Answer.objects.create(question=question, **answer_data)
        
        return question
    
    def update(self, instance, validated_data):
        answers_data = validated_data.pop('answers', [])
        
        # Update question fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update answers
        if answers_data:
            # Delete existing answers and create new ones
            instance.answers.all().delete()
            for answer_data in answers_data:
                Answer.objects.create(question=instance, **answer_data)
        
        return instance


class TestListSerializer(serializers.ModelSerializer):
    """Serializer for test list view."""
    
    course_title = serializers.CharField(source='course.title', read_only=True)
    instructor_name = serializers.SerializerMethodField()
    question_count = serializers.SerializerMethodField()
    is_available = serializers.SerializerMethodField()
    
    class Meta:
        model = Test
        fields = [
            'id', 'title', 'description', 'test_type', 'status', 'course',
            'course_title', 'instructor_name', 'time_limit', 'available_from',
            'available_until', 'max_attempts', 'passing_score', 'total_points',
            'question_count', 'is_available', 'created_at'
        ]
        read_only_fields = [
            'id', 'course_title', 'instructor_name', 'question_count',
            'is_available', 'created_at'
        ]
    
    @extend_schema_field(serializers.CharField)
    def get_instructor_name(self, obj):
        return f"{obj.instructor.first_name} {obj.instructor.last_name}"
    
    @extend_schema_field(serializers.IntegerField)
    def get_question_count(self, obj):
        return obj.questions.count()
    
    @extend_schema_field(serializers.BooleanField)
    def get_is_available(self, obj):
        return obj.is_available


class TestDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for tests with questions."""
    
    course_title = serializers.CharField(source='course.title', read_only=True)
    instructor_name = serializers.SerializerMethodField()
    questions = QuestionListSerializer(many=True, read_only=True)
    is_available = serializers.SerializerMethodField()
    has_time_limit = serializers.SerializerMethodField()
    
    class Meta:
        model = Test
        fields = [
            'id', 'title', 'description', 'test_type', 'status', 'course',
            'lesson', 'instructor', 'course_title', 'instructor_name',
            'time_limit', 'available_from', 'available_until', 'max_attempts',
            'allow_review', 'show_correct_answers', 'show_score_immediately',
            'grading_method', 'passing_score', 'total_points',
            'randomize_questions', 'randomize_answers', 'questions_per_page',
            'require_password', 'access_password', 'ip_restrictions',
            'require_webcam', 'prevent_copy_paste', 'full_screen_mode',
            'total_attempts', 'average_score', 'questions', 'is_available',
            'has_time_limit', 'created_at', 'updated_at', 'published_at'
        ]
        read_only_fields = [
            'id', 'instructor', 'course_title', 'instructor_name',
            'total_attempts', 'average_score', 'is_available',
            'has_time_limit', 'created_at', 'updated_at', 'published_at'
        ]
    
    @extend_schema_field(serializers.CharField)
    def get_instructor_name(self, obj):
        return f"{obj.instructor.first_name} {obj.instructor.last_name}"
    
    @extend_schema_field(serializers.BooleanField)
    def get_is_available(self, obj):
        return obj.is_available
    
    @extend_schema_field(serializers.BooleanField)
    def get_has_time_limit(self, obj):
        return obj.has_time_limit


class TestCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating tests."""
    
    class Meta:
        model = Test
        fields = [
            'title', 'description', 'test_type', 'status', 'course', 'lesson',
            'time_limit', 'available_from', 'available_until', 'max_attempts',
            'allow_review', 'show_correct_answers', 'show_score_immediately',
            'grading_method', 'passing_score', 'randomize_questions',
            'randomize_answers', 'questions_per_page', 'require_password',
            'access_password', 'ip_restrictions', 'require_webcam',
            'prevent_copy_paste', 'full_screen_mode'
        ]
    
    def create(self, validated_data):
        # Set instructor from request user
        request = self.context.get('request')
        if request and request.user:
            validated_data['instructor'] = request.user
        return super().create(validated_data)


class QuestionResponseSerializer(serializers.ModelSerializer):
    """Serializer for question responses."""
    
    question_text = serializers.CharField(source='question.question_text', read_only=True)
    selected_answer_texts = serializers.SerializerMethodField()
    
    class Meta:
        model = QuestionResponse
        fields = [
            'id', 'question', 'question_text', 'selected_answers',
            'selected_answer_texts', 'text_response', 'file_response',
            'response_data', 'points_earned', 'is_correct', 'is_graded',
            'feedback', 'time_spent'
        ]
        read_only_fields = [
            'id', 'question_text', 'selected_answer_texts', 'points_earned',
            'is_correct', 'is_graded', 'feedback'
        ]
    
    @extend_schema_field(serializers.ListField(child=serializers.CharField()))
    def get_selected_answer_texts(self, obj):
        return [answer.answer_text for answer in obj.selected_answers.all()]


class TestAttemptSerializer(serializers.ModelSerializer):
    """Serializer for test attempts."""
    
    test_title = serializers.CharField(source='test.title', read_only=True)
    student_name = serializers.SerializerMethodField()
    responses = QuestionResponseSerializer(many=True, read_only=True)
    is_expired = serializers.SerializerMethodField()
    time_remaining = serializers.SerializerMethodField()
    
    class Meta:
        model = TestAttempt
        fields = [
            'id', 'test', 'test_title', 'student', 'student_name',
            'attempt_number', 'status', 'started_at', 'submitted_at',
            'time_spent', 'expires_at', 'score', 'percentage', 'is_passed',
            'auto_graded', 'manually_graded', 'graded_by', 'graded_at',
            'instructor_feedback', 'responses', 'is_expired', 'time_remaining'
        ]
        read_only_fields = [
            'id', 'test_title', 'student_name', 'attempt_number', 'started_at',
            'submitted_at', 'time_spent', 'expires_at', 'score', 'percentage',
            'is_passed', 'auto_graded', 'manually_graded', 'graded_by',
            'graded_at', 'is_expired', 'time_remaining'
        ]
    
    @extend_schema_field(serializers.CharField)
    def get_student_name(self, obj):
        return f"{obj.student.first_name} {obj.student.last_name}"
    
    @extend_schema_field(serializers.BooleanField)
    def get_is_expired(self, obj):
        return obj.is_expired
    
    @extend_schema_field(serializers.IntegerField)
    def get_time_remaining(self, obj):
        return obj.time_remaining


class TestResultSerializer(serializers.ModelSerializer):
    """Serializer for test results."""
    
    test_title = serializers.CharField(source='test.title', read_only=True)
    student_name = serializers.SerializerMethodField()
    
    class Meta:
        model = TestResult
        fields = [
            'id', 'test', 'test_title', 'student', 'student_name',
            'best_attempt', 'best_score', 'best_percentage', 'total_attempts',
            'average_score', 'first_attempt_score', 'is_passed',
            'is_completed', 'total_time_spent', 'first_completed_at',
            'last_attempt_at'
        ]
        read_only_fields = [
            'id', 'test_title', 'student_name', 'best_attempt', 'best_score',
            'best_percentage', 'total_attempts', 'average_score',
            'first_attempt_score', 'is_passed', 'is_completed',
            'total_time_spent', 'first_completed_at', 'last_attempt_at'
        ]
    
    @extend_schema_field(serializers.CharField)
    def get_student_name(self, obj):
        return f"{obj.student.first_name} {obj.student.last_name}"


class BankAnswerSerializer(serializers.ModelSerializer):
    """Serializer for question bank answers."""
    
    class Meta:
        model = BankAnswer
        fields = ['id', 'answer_text', 'is_correct', 'order', 'points']
        read_only_fields = ['id']


class BankQuestionSerializer(serializers.ModelSerializer):
    """Serializer for question bank questions."""
    
    answers = BankAnswerSerializer(many=True, read_only=True)
    
    class Meta:
        model = BankQuestion
        fields = [
            'id', 'bank', 'question_text', 'question_type', 'points',
            'difficulty', 'image', 'explanation', 'tags', 'usage_count',
            'answers', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'usage_count', 'created_at', 'updated_at']


class QuestionBankSerializer(serializers.ModelSerializer):
    """Serializer for question banks."""
    
    question_count = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = QuestionBank
        fields = [
            'id', 'name', 'description', 'course', 'created_by',
            'created_by_name', 'is_public', 'tags', 'question_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_by', 'created_by_name', 'question_count',
            'created_at', 'updated_at'
        ]
    
    @extend_schema_field(serializers.IntegerField)
    def get_question_count(self, obj):
        return obj.questions.count()
    
    @extend_schema_field(serializers.CharField)
    def get_created_by_name(self, obj):
        return f"{obj.created_by.first_name} {obj.created_by.last_name}"
    
    def create(self, validated_data):
        # Set created_by from request user
        request = self.context.get('request')
        if request and request.user:
            validated_data['created_by'] = request.user
        return super().create(validated_data) 
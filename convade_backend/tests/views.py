from django.shortcuts import render
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Avg
from django.utils import timezone
from decimal import Decimal
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from .models import (
    Test, Question, Answer, TestAttempt, QuestionResponse,
    TestResult, QuestionBank, BankQuestion, BankAnswer
)
from .serializers import (
    TestListSerializer, TestDetailSerializer, TestCreateUpdateSerializer,
    QuestionListSerializer, QuestionDetailSerializer, QuestionCreateUpdateSerializer,
    TestAttemptSerializer, QuestionResponseSerializer, TestResultSerializer,
    QuestionBankSerializer, BankQuestionSerializer
)
from courses.models import Enrollment
from courses.permissions import IsInstructorOrReadOnly


@extend_schema_view(
    list=extend_schema(
        summary="List tests",
        description="Get a list of tests based on user permissions",
        parameters=[
            OpenApiParameter(
                name='test_type',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by test type'
            ),
            OpenApiParameter(
                name='status',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by test status'
            ),
            OpenApiParameter(
                name='course',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.QUERY,
                description='Filter by course UUID'
            ),
            OpenApiParameter(
                name='grading_method',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by grading method'
            ),
            OpenApiParameter(
                name='search',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Search in title, description, and course title'
            ),
            OpenApiParameter(
                name='ordering',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Order by field (title, created_at, available_from, total_attempts)'
            ),
        ]
    ),
    retrieve=extend_schema(
        summary="Get test details",
        description="Retrieve detailed information about a specific test",
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description='Test UUID'
            )
        ]
    ),
    create=extend_schema(
        summary="Create test",
        description="Create a new test"
    ),
    update=extend_schema(
        summary="Update test",
        description="Update an existing test",
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description='Test UUID'
            )
        ]
    ),
    partial_update=extend_schema(
        summary="Partially update test",
        description="Partially update an existing test",
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description='Test UUID'
            )
        ]
    ),
    destroy=extend_schema(
        summary="Delete test",
        description="Delete a test",
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description='Test UUID'
            )
        ]
    ),
)
class TestViewSet(viewsets.ModelViewSet):
    """ViewSet for tests/quizzes with comprehensive CRUD operations."""
    
    permission_classes = [IsInstructorOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['test_type', 'status', 'course', 'grading_method']
    search_fields = ['title', 'description', 'course__title']
    ordering_fields = ['title', 'created_at', 'available_from', 'total_attempts']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter tests based on user permissions."""
        user = self.request.user
        
        # Handle schema generation and anonymous users
        if getattr(self, 'swagger_fake_view', False):
            return Test.objects.none()
        
        if not user.is_authenticated:
            return Test.objects.none()
        
        if user.is_teacher:
            # Teachers can see their own tests
            return Test.objects.filter(instructor=user).select_related(
                'course', 'lesson', 'instructor'
            ).prefetch_related('questions')
        else:
            # Students see published tests for enrolled courses
            enrolled_courses = Enrollment.objects.filter(
                student=user, 
                status=Enrollment.ACTIVE
            ).values_list('course_id', flat=True)
            
            return Test.objects.filter(
                course_id__in=enrolled_courses,
                status=Test.PUBLISHED
            ).select_related('course', 'lesson', 'instructor')
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return TestListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return TestCreateUpdateSerializer
        return TestDetailSerializer
    
    def perform_create(self, serializer):
        """Set instructor when creating a test."""
        serializer.save(instructor=self.request.user)
    
    @extend_schema(
        summary="Start test attempt",
        description="Start a new test attempt for the authenticated user",
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description='Test UUID'
            )
        ],
        responses={
            201: TestAttemptSerializer,
            400: OpenApiTypes.OBJECT,
            403: OpenApiTypes.OBJECT
        }
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def start_attempt(self, request, pk=None):
        """Start a new test attempt."""
        test = self.get_object()
        student = request.user
        
        # Check if student is enrolled in the course
        if not Enrollment.objects.filter(
            student=student, 
            course=test.course, 
            status=Enrollment.ACTIVE
        ).exists():
            return Response(
                {'error': 'Not enrolled in this course'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if test is available
        if not test.is_available:
            return Response(
                {'error': 'Test is not available'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check attempt limits
        existing_attempts = TestAttempt.objects.filter(
            test=test, student=student
        ).count()
        
        if existing_attempts >= test.max_attempts:
            return Response(
                {'error': 'Maximum attempts reached'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check for existing in-progress attempt
        in_progress = TestAttempt.objects.filter(
            test=test, 
            student=student, 
            status=TestAttempt.IN_PROGRESS
        ).first()
        
        if in_progress:
            serializer = TestAttemptSerializer(in_progress)
            return Response(serializer.data)
        
        # Create new attempt
        attempt = TestAttempt.objects.create(
            test=test,
            student=student,
            attempt_number=existing_attempts + 1,
            status=TestAttempt.IN_PROGRESS,
            started_at=timezone.now()
        )
        
        # Set expiration time if test has time limit
        if test.has_time_limit:
            attempt.expires_at = timezone.now() + timezone.timedelta(minutes=test.time_limit)
            attempt.save()
        
        # Update test attempt count
        test.total_attempts += 1
        test.save(update_fields=['total_attempts'])
        
        serializer = TestAttemptSerializer(attempt)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @extend_schema(
        summary="Get user's test attempts",
        description="Get all attempts for this test by the current user",
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description='Test UUID'
            )
        ],
        responses={200: TestAttemptSerializer(many=True)}
    )
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def my_attempts(self, request, pk=None):
        """Get current user's attempts for this test."""
        test = self.get_object()
        attempts = TestAttempt.objects.filter(
            test=test, student=request.user
        ).order_by('-attempt_number')
        
        serializer = TestAttemptSerializer(attempts, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Get all test attempts",
        description="Get all attempts for this test (instructor only)",
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description='Test UUID'
            )
        ],
        responses={200: TestAttemptSerializer(many=True)}
    )
    @action(detail=True, methods=['get'], permission_classes=[IsInstructorOrReadOnly])
    def attempts(self, request, pk=None):
        """Get all attempts for this test (instructor only)."""
        test = self.get_object()
        attempts = test.attempts.select_related('student').order_by('-started_at')
        serializer = TestAttemptSerializer(attempts, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Get test analytics",
        description="Get comprehensive analytics for this test (instructor only)",
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description='Test UUID'
            )
        ],
        responses={
            200: OpenApiTypes.OBJECT
        }
    )
    @action(detail=True, methods=['get'], permission_classes=[IsInstructorOrReadOnly])
    def analytics(self, request, pk=None):
        """Get test analytics (instructor only)."""
        test = self.get_object()
        
        attempts = test.attempts.filter(status=TestAttempt.GRADED)
        
        analytics_data = {
            'total_attempts': test.total_attempts,
            'completed_attempts': attempts.count(),
            'average_score': test.average_score,
            'pass_rate': attempts.filter(is_passed=True).count() / max(attempts.count(), 1) * 100,
            'question_count': test.questions.count(),
            'total_points': test.total_points,
            'difficulty_distribution': test.questions.values('difficulty').annotate(
                count=Count('id')
            ),
            'question_type_distribution': test.questions.values('question_type').annotate(
                count=Count('id')
            )
        }
        
        return Response(analytics_data)


@extend_schema_view(
    list=extend_schema(
        summary="List questions",
        description="Get a list of questions based on user permissions and filters",
        parameters=[
            OpenApiParameter(
                name='test',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.QUERY,
                description='Filter questions by test UUID'
            ),
            OpenApiParameter(
                name='question_type',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by question type (multiple_choice, true_false, short_answer, essay, fill_blank, matching)'
            ),
            OpenApiParameter(
                name='difficulty',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by difficulty level (easy, medium, hard)'
            ),
            OpenApiParameter(
                name='ordering',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Order by field (order, points, created_at)'
            ),
        ]
    ),
    retrieve=extend_schema(
        summary="Get question details",
        description="Retrieve detailed information about a specific question",
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description='Question UUID'
            )
        ]
    ),
    create=extend_schema(
        summary="Create question",
        description="Create a new question for a test"
    ),
    update=extend_schema(
        summary="Update question",
        description="Update an existing question",
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description='Question UUID'
            )
        ]
    ),
    partial_update=extend_schema(
        summary="Partially update question",
        description="Partially update an existing question",
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description='Question UUID'
            )
        ]
    ),
    destroy=extend_schema(
        summary="Delete question",
        description="Delete a question",
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description='Question UUID'
            )
        ]
    ),
)
class QuestionViewSet(viewsets.ModelViewSet):
    """ViewSet for test questions."""
    
    permission_classes = [IsInstructorOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['question_type', 'difficulty', 'test']
    ordering_fields = ['order', 'points', 'created_at']
    ordering = ['order']
    
    def get_queryset(self):
        """Filter questions based on test and user permissions."""
        test_id = self.request.query_params.get('test')
        if test_id:
            return Question.objects.filter(test_id=test_id).select_related('test')
        return Question.objects.all().select_related('test')
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return QuestionListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return QuestionCreateUpdateSerializer
        return QuestionDetailSerializer
    
    def perform_create(self, serializer):
        """Update test total points when creating a question."""
        question = serializer.save()
        question.test.calculate_total_points()
    
    def perform_update(self, serializer):
        """Update test total points when updating a question."""
        question = serializer.save()
        question.test.calculate_total_points()
    
    def perform_destroy(self, instance):
        """Update test total points when deleting a question."""
        test = instance.test
        super().perform_destroy(instance)
        test.calculate_total_points()


@extend_schema_view(
    list=extend_schema(
        summary="List test attempts",
        description="Get a list of test attempts based on user permissions",
        parameters=[
            OpenApiParameter(
                name='status',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by attempt status (in_progress, submitted, graded, expired)'
            ),
            OpenApiParameter(
                name='test',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.QUERY,
                description='Filter by test UUID'
            ),
            OpenApiParameter(
                name='is_passed',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description='Filter by pass/fail status'
            ),
            OpenApiParameter(
                name='ordering',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Order by field (started_at, submitted_at, score)'
            ),
        ]
    ),
    retrieve=extend_schema(
        summary="Get test attempt details",
        description="Retrieve detailed information about a specific test attempt",
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description='Test attempt UUID'
            )
        ]
    ),
    update=extend_schema(
        summary="Update test attempt",
        description="Update a test attempt",
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description='Test attempt UUID'
            )
        ]
    ),
    partial_update=extend_schema(
        summary="Partially update test attempt",
        description="Partially update a test attempt",
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description='Test attempt UUID'
            )
        ]
    ),
)
class TestAttemptViewSet(viewsets.ModelViewSet):
    """ViewSet for test attempts."""
    
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'test', 'is_passed']
    ordering_fields = ['started_at', 'submitted_at', 'score']
    ordering = ['-started_at']
    
    def get_queryset(self):
        """Filter test attempts based on user permissions."""
        user = self.request.user
        
        # Handle schema generation and anonymous users
        if getattr(self, 'swagger_fake_view', False):
            return TestAttempt.objects.none()
        
        if not user.is_authenticated:
            return TestAttempt.objects.none()
        
        if user.is_teacher:
            # Teachers can see attempts for their tests
            return TestAttempt.objects.filter(
                test__instructor=user
            ).select_related('test', 'student').order_by('-started_at')
        else:
            # Students can only see their own attempts
            return TestAttempt.objects.filter(
                student=user
            ).select_related('test', 'student').order_by('-started_at')
    
    def get_serializer_class(self):
        return TestAttemptSerializer
    
    @extend_schema(
        summary="Submit response to question",
        description="Submit or update a response to a specific question in this attempt",
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description='Test attempt UUID'
            )
        ],
        request=OpenApiTypes.OBJECT,
        responses={
            200: QuestionResponseSerializer,
            400: OpenApiTypes.OBJECT,
            403: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT
        }
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def submit_response(self, request, pk=None):
        """Submit a response to a question in this attempt."""
        attempt = self.get_object()
        
        # Check if this is the student's attempt
        if attempt.student != request.user:
            return Response(
                {'error': 'Not authorized'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if attempt is still in progress
        if attempt.status != TestAttempt.IN_PROGRESS:
            return Response(
                {'error': 'Attempt is not in progress'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if attempt has expired
        if attempt.is_expired:
            attempt.status = TestAttempt.EXPIRED
            attempt.save()
            return Response(
                {'error': 'Attempt has expired'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        question_id = request.data.get('question_id')
        if not question_id:
            return Response(
                {'error': 'Question ID is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            question = Question.objects.get(id=question_id, test=attempt.test)
        except Question.DoesNotExist:
            return Response(
                {'error': 'Question not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get or create response
        response, created = QuestionResponse.objects.get_or_create(
            attempt=attempt,
            question=question,
            defaults={
                'text_response': request.data.get('text_response', ''),
                'response_data': request.data.get('response_data', {}),
                'time_spent': request.data.get('time_spent', 0)
            }
        )
        
        if not created:
            # Update existing response
            response.text_response = request.data.get('text_response', response.text_response)
            response.response_data = request.data.get('response_data', response.response_data)
            response.time_spent = request.data.get('time_spent', response.time_spent)
        
        # Handle selected answers
        selected_answer_ids = request.data.get('selected_answers', [])
        if selected_answer_ids:
            response.selected_answers.set(selected_answer_ids)
        
        response.save()
        
        # Auto-grade if possible
        response.auto_grade()
        
        serializer = QuestionResponseSerializer(response)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Submit test attempt",
        description="Submit the entire test attempt for grading",
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description='Test attempt UUID'
            )
        ],
        responses={
            200: TestAttemptSerializer,
            400: OpenApiTypes.OBJECT,
            403: OpenApiTypes.OBJECT
        }
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def submit_attempt(self, request, pk=None):
        """Submit the entire test attempt."""
        attempt = self.get_object()
        
        # Check if this is the student's attempt
        if attempt.student != request.user:
            return Response(
                {'error': 'Not authorized'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if attempt is still in progress
        if attempt.status != TestAttempt.IN_PROGRESS:
            return Response(
                {'error': 'Attempt is not in progress'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Submit the attempt
        attempt.status = TestAttempt.SUBMITTED
        attempt.submitted_at = timezone.now()
        attempt.time_spent = (attempt.submitted_at - attempt.started_at).total_seconds()
        
        # Calculate score
        attempt.calculate_score()
        attempt.save()
        
        # Update or create test result
        result, created = TestResult.objects.get_or_create(
            test=attempt.test,
            student=attempt.student,
            defaults={
                'best_attempt': attempt,
                'best_score': attempt.score,
                'best_percentage': attempt.percentage,
                'total_attempts': 1,
                'average_score': attempt.score,
                'first_attempt_score': attempt.score,
                'is_passed': attempt.is_passed,
                'is_completed': True,
                'total_time_spent': attempt.time_spent,
                'first_completed_at': attempt.submitted_at,
                'last_attempt_at': attempt.submitted_at
            }
        )
        
        if not created:
            result.update_from_attempts()
        
        serializer = TestAttemptSerializer(attempt)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Manually grade attempt",
        description="Manually grade an attempt and provide feedback (instructor only)",
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description='Test attempt UUID'
            )
        ],
        request=OpenApiTypes.OBJECT,
        responses={200: TestAttemptSerializer}
    )
    @action(detail=True, methods=['post'], permission_classes=[IsInstructorOrReadOnly])
    def grade_manually(self, request, pk=None):
        """Manually grade an attempt (instructor only)."""
        attempt = self.get_object()
        
        # Update instructor feedback
        feedback = request.data.get('instructor_feedback', '')
        if feedback:
            attempt.instructor_feedback = feedback
        
        # Update individual response grades
        response_grades = request.data.get('response_grades', [])
        for grade_data in response_grades:
            try:
                response = QuestionResponse.objects.get(
                    id=grade_data['response_id'],
                    attempt=attempt
                )
                response.points_earned = Decimal(str(grade_data['points_earned']))
                response.feedback = grade_data.get('feedback', '')
                response.is_graded = True
                response.save()
            except (QuestionResponse.DoesNotExist, KeyError, ValueError):
                continue
        
        # Recalculate total score
        attempt.calculate_score()
        attempt.manually_graded = True
        attempt.graded_by = request.user
        attempt.graded_at = timezone.now()
        attempt.save()
        
        # Update test result
        try:
            result = TestResult.objects.get(test=attempt.test, student=attempt.student)
            result.update_from_attempts()
        except TestResult.DoesNotExist:
            pass
        
        serializer = TestAttemptSerializer(attempt)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(
        summary="List test results",
        description="Get a list of test results based on user permissions",
        parameters=[
            OpenApiParameter(
                name='test',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.QUERY,
                description='Filter by test UUID'
            ),
            OpenApiParameter(
                name='is_passed',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description='Filter by pass/fail status'
            ),
            OpenApiParameter(
                name='is_completed',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description='Filter by completion status'
            ),
            OpenApiParameter(
                name='ordering',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Order by field (best_percentage, last_attempt_at, total_attempts)'
            ),
        ]
    ),
    retrieve=extend_schema(
        summary="Get test result details",
        description="Retrieve detailed information about a specific test result",
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description='Test result UUID'
            )
        ]
    ),
)
class TestResultViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing test results."""
    
    serializer_class = TestResultSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['test', 'is_passed', 'is_completed']
    ordering_fields = ['best_percentage', 'last_attempt_at', 'total_attempts']
    ordering = ['-last_attempt_at']
    
    def get_queryset(self):
        """Return results for the current user or instructor's tests."""
        user = self.request.user
        
        # Handle schema generation and anonymous users
        if getattr(self, 'swagger_fake_view', False):
            return TestResult.objects.none()
        
        if not user.is_authenticated:
            return TestResult.objects.none()
        
        if user.is_teacher:
            # Teachers can see results for their tests
            return TestResult.objects.filter(
                test__instructor=user
            ).select_related('test', 'student', 'best_attempt')
        else:
            # Students can only see their own results
            return TestResult.objects.filter(
                student=user
            ).select_related('test', 'best_attempt')


@extend_schema_view(
    list=extend_schema(
        summary="List question banks",
        description="Get a list of question banks based on user permissions",
        parameters=[
            OpenApiParameter(
                name='course',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.QUERY,
                description='Filter by course UUID'
            ),
            OpenApiParameter(
                name='is_public',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description='Filter by public visibility'
            ),
            OpenApiParameter(
                name='search',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Search in name, description, and tags'
            ),
            OpenApiParameter(
                name='ordering',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Order by field (name, created_at)'
            ),
        ]
    ),
    retrieve=extend_schema(
        summary="Get question bank details",
        description="Retrieve detailed information about a specific question bank",
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description='Question bank UUID'
            )
        ]
    ),
    create=extend_schema(
        summary="Create question bank",
        description="Create a new question bank"
    ),
    update=extend_schema(
        summary="Update question bank",
        description="Update an existing question bank",
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description='Question bank UUID'
            )
        ]
    ),
    partial_update=extend_schema(
        summary="Partially update question bank",
        description="Partially update an existing question bank",
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description='Question bank UUID'
            )
        ]
    ),
    destroy=extend_schema(
        summary="Delete question bank",
        description="Delete a question bank",
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description='Question bank UUID'
            )
        ]
    ),
)
class QuestionBankViewSet(viewsets.ModelViewSet):
    """ViewSet for question banks."""
    
    serializer_class = QuestionBankSerializer
    permission_classes = [IsInstructorOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['course', 'is_public']
    search_fields = ['name', 'description', 'tags']
    ordering_fields = ['name', 'created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter question banks based on user permissions."""
        user = self.request.user
        
        if user.is_authenticated and user.is_teacher:
            # Teachers can see their own banks and public ones
            return QuestionBank.objects.filter(
                Q(created_by=user) | Q(is_public=True)
            ).select_related('course', 'created_by')
        else:
            # Students can only see public banks
            return QuestionBank.objects.filter(
                is_public=True
            ).select_related('course', 'created_by')
    
    def perform_create(self, serializer):
        """Set created_by when creating a question bank."""
        serializer.save(created_by=self.request.user)
    
    @extend_schema(
        summary="Get questions in bank",
        description="Retrieve all questions in this question bank",
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description='Question bank UUID'
            )
        ],
        responses={200: BankQuestionSerializer(many=True)}
    )
    @action(detail=True, methods=['get'])
    def questions(self, request, pk=None):
        """Get questions in this bank."""
        bank = self.get_object()
        questions = bank.questions.order_by('-created_at')
        serializer = BankQuestionSerializer(questions, many=True)
        return Response(serializer.data)

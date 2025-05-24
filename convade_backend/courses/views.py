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

from .models import (
    Category, Course, Module, Lesson, Enrollment, 
    LessonProgress, Announcement
)
from .serializers import (
    CategorySerializer, CourseListSerializer, CourseDetailSerializer,
    CourseCreateUpdateSerializer, ModuleListSerializer, ModuleDetailSerializer,
    LessonListSerializer, LessonDetailSerializer, EnrollmentSerializer,
    LessonProgressSerializer, AnnouncementSerializer
)
from .permissions import IsInstructorOrReadOnly, IsEnrolledStudent


class CategoryViewSet(viewsets.ModelViewSet):
    """ViewSet for course categories."""
    
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'sort_order', 'created_at']
    ordering = ['sort_order', 'name']


class CourseViewSet(viewsets.ModelViewSet):
    """ViewSet for courses with comprehensive CRUD operations."""
    
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'difficulty', 'is_free', 'status']
    search_fields = ['title', 'description', 'course_code', 'instructor__first_name', 'instructor__last_name']
    ordering_fields = ['title', 'created_at', 'enrollment_count', 'completion_rate']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter courses based on user permissions."""
        user = self.request.user
        
        if user.is_authenticated and user.is_teacher:
            # Teachers can see their own courses regardless of status
            return Course.objects.filter(instructor=user).select_related(
                'category', 'instructor', 'school'
            ).prefetch_related('modules', 'prerequisites')
        else:
            # Students and anonymous users only see published courses
            return Course.objects.filter(status=Course.PUBLISHED).select_related(
                'category', 'instructor', 'school'
            ).prefetch_related('modules', 'prerequisites')
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return CourseListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return CourseCreateUpdateSerializer
        return CourseDetailSerializer
    
    def perform_create(self, serializer):
        """Set instructor and school when creating a course."""
        serializer.save(instructor=self.request.user, school=self.request.user.profile.school if hasattr(self.request.user, 'profile') else None)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def enroll(self, request, pk=None):
        """Enroll a student in a course."""
        course = self.get_object()
        student = request.user
        
        # Check if already enrolled
        if Enrollment.objects.filter(student=student, course=course).exists():
            return Response(
                {'error': 'Already enrolled in this course'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check enrollment eligibility
        if not course.is_enrollment_open:
            return Response(
                {'error': 'Enrollment is not open for this course'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if course.available_slots <= 0:
            return Response(
                {'error': 'Course is full'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create enrollment
        enrollment_status = Enrollment.PENDING if course.requires_approval else Enrollment.ACTIVE
        enrollment = Enrollment.objects.create(
            student=student,
            course=course,
            status=enrollment_status
        )
        
        # Update course enrollment count
        course.enrollment_count += 1
        course.save(update_fields=['enrollment_count'])
        
        serializer = EnrollmentSerializer(enrollment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['delete'], permission_classes=[IsAuthenticated])
    def unenroll(self, request, pk=None):
        """Unenroll a student from a course."""
        course = self.get_object()
        student = request.user
        
        try:
            enrollment = Enrollment.objects.get(student=student, course=course)
            enrollment.status = Enrollment.DROPPED
            enrollment.save()
            
            # Update course enrollment count
            course.enrollment_count = max(0, course.enrollment_count - 1)
            course.save(update_fields=['enrollment_count'])
            
            return Response({'message': 'Successfully unenrolled'}, status=status.HTTP_200_OK)
        except Enrollment.DoesNotExist:
            return Response(
                {'error': 'Not enrolled in this course'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def progress(self, request, pk=None):
        """Get student's progress in a course."""
        course = self.get_object()
        student = request.user
        
        try:
            enrollment = Enrollment.objects.get(student=student, course=course)
            serializer = EnrollmentSerializer(enrollment)
            return Response(serializer.data)
        except Enrollment.DoesNotExist:
            return Response(
                {'error': 'Not enrolled in this course'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['get'])
    def modules(self, request, pk=None):
        """Get course modules."""
        course = self.get_object()
        modules = course.modules.filter(is_published=True).order_by('order')
        serializer = ModuleListSerializer(modules, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], permission_classes=[IsInstructorOrReadOnly])
    def enrollments(self, request, pk=None):
        """Get course enrollments (instructor only)."""
        course = self.get_object()
        enrollments = course.enrollments.select_related('student').order_by('-enrollment_date')
        serializer = EnrollmentSerializer(enrollments, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], permission_classes=[IsInstructorOrReadOnly])
    def analytics(self, request, pk=None):
        """Get course analytics (instructor only)."""
        course = self.get_object()
        
        analytics_data = {
            'total_enrollments': course.enrollment_count,
            'active_enrollments': course.enrollments.filter(status=Enrollment.ACTIVE).count(),
            'completed_enrollments': course.enrollments.filter(status=Enrollment.COMPLETED).count(),
            'completion_rate': course.completion_rate,
            'average_grade': course.enrollments.filter(
                final_grade__isnull=False
            ).aggregate(avg_grade=Avg('final_grade'))['avg_grade'] or 0,
            'view_count': course.view_count,
            'module_count': course.modules.filter(is_published=True).count(),
            'lesson_count': sum(
                module.lessons.filter(is_published=True).count() 
                for module in course.modules.filter(is_published=True)
            )
        }
        
        return Response(analytics_data)


class ModuleViewSet(viewsets.ModelViewSet):
    """ViewSet for course modules."""
    
    permission_classes = [IsInstructorOrReadOnly]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['order', 'title', 'created_at']
    ordering = ['order']
    
    def get_queryset(self):
        """Filter modules based on course and user permissions."""
        course_id = self.request.query_params.get('course')
        if course_id:
            return Module.objects.filter(course_id=course_id).select_related('course')
        return Module.objects.all().select_related('course')
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return ModuleListSerializer
        return ModuleDetailSerializer
    
    @action(detail=True, methods=['get'])
    def lessons(self, request, pk=None):
        """Get module lessons."""
        module = self.get_object()
        lessons = module.lessons.filter(is_published=True).order_by('order')
        serializer = LessonListSerializer(lessons, many=True)
        return Response(serializer.data)


class LessonViewSet(viewsets.ModelViewSet):
    """ViewSet for lessons."""
    
    permission_classes = [IsInstructorOrReadOnly]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['order', 'title', 'created_at']
    ordering = ['order']
    
    def get_queryset(self):
        """Filter lessons based on module and user permissions."""
        module_id = self.request.query_params.get('module')
        if module_id:
            return Lesson.objects.filter(module_id=module_id).select_related('module')
        return Lesson.objects.all().select_related('module')
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return LessonListSerializer
        return LessonDetailSerializer
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def mark_complete(self, request, pk=None):
        """Mark a lesson as completed for the current user."""
        lesson = self.get_object()
        student = request.user
        
        # Get or create enrollment
        try:
            enrollment = Enrollment.objects.get(
                student=student, 
                course=lesson.module.course,
                status=Enrollment.ACTIVE
            )
        except Enrollment.DoesNotExist:
            return Response(
                {'error': 'Not enrolled in this course'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get or create lesson progress
        progress, created = LessonProgress.objects.get_or_create(
            enrollment=enrollment,
            lesson=lesson,
            defaults={
                'status': LessonProgress.COMPLETED,
                'started_at': timezone.now(),
                'completed_at': timezone.now(),
                'completion_percentage': 100.00
            }
        )
        
        if not created and progress.status != LessonProgress.COMPLETED:
            progress.status = LessonProgress.COMPLETED
            progress.completed_at = timezone.now()
            progress.completion_percentage = 100.00
            progress.save()
        
        # Update lesson view count
        lesson.view_count += 1
        lesson.save(update_fields=['view_count'])
        
        # Update enrollment progress
        self._update_enrollment_progress(enrollment)
        
        serializer = LessonProgressSerializer(progress)
        return Response(serializer.data)
    
    def _update_enrollment_progress(self, enrollment):
        """Update overall enrollment progress based on completed lessons."""
        course = enrollment.course
        total_lessons = sum(
            module.lessons.filter(is_published=True).count()
            for module in course.modules.filter(is_published=True)
        )
        
        if total_lessons > 0:
            completed_lessons = LessonProgress.objects.filter(
                enrollment=enrollment,
                status=LessonProgress.COMPLETED
            ).count()
            
            progress_percentage = (completed_lessons / total_lessons) * 100
            enrollment.progress_percentage = round(progress_percentage, 2)
            enrollment.last_accessed = timezone.now()
            
            # Mark as completed if all lessons are done
            if progress_percentage >= 100:
                enrollment.status = Enrollment.COMPLETED
                enrollment.completion_date = timezone.now()
                
                # Update course completion count
                course.completion_count += 1
                course.save(update_fields=['completion_count'])
            
            enrollment.save()


class EnrollmentViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing enrollments."""
    
    serializer_class = EnrollmentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'course__category']
    ordering_fields = ['enrollment_date', 'progress_percentage', 'current_grade']
    ordering = ['-enrollment_date']
    
    def get_queryset(self):
        """Return enrollments for the current user."""
        user = self.request.user
        
        # Handle schema generation and anonymous users
        if getattr(self, 'swagger_fake_view', False):
            return Enrollment.objects.none()
        
        if not user.is_authenticated:
            return Enrollment.objects.none()
        
        return Enrollment.objects.filter(
            student=user
        ).select_related('course', 'course__category', 'course__instructor')


class AnnouncementViewSet(viewsets.ModelViewSet):
    """ViewSet for course announcements."""
    
    serializer_class = AnnouncementSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['course', 'is_urgent', 'is_published']
    ordering_fields = ['created_at', 'is_urgent']
    ordering = ['-is_urgent', '-created_at']
    
    def get_queryset(self):
        """Filter announcements based on user role."""
        user = self.request.user
        
        # Handle schema generation and anonymous users
        if getattr(self, 'swagger_fake_view', False):
            return Announcement.objects.none()
        
        if not user.is_authenticated:
            return Announcement.objects.none()
        
        if user.is_teacher:
            # Teachers see announcements for their courses
            return Announcement.objects.filter(
                course__instructor=user
            ).select_related('course', 'instructor')
        else:
            # Students see announcements for enrolled courses
            enrolled_courses = Enrollment.objects.filter(
                student=user, 
                status=Enrollment.ACTIVE
            ).values_list('course_id', flat=True)
            
            return Announcement.objects.filter(
                course_id__in=enrolled_courses,
                is_published=True
            ).filter(
                Q(target_all_students=True) | Q(target_students=user)
            ).select_related('course', 'instructor')
    
    def perform_create(self, serializer):
        """Set instructor when creating an announcement."""
        serializer.save(instructor=self.request.user)

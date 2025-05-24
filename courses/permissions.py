from rest_framework import permissions
from .models import Enrollment


class IsInstructorOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow teachers to edit courses/modules/lessons.
    """
    
    def has_permission(self, request, view):
        # Read permissions for any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        
        # Write permissions only for teachers
        return request.user.is_authenticated and request.user.is_teacher
    
    def has_object_permission(self, request, view, obj):
        # Read permissions for any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only for the teacher who owns the content
        if hasattr(obj, 'instructor'):
            return obj.instructor == request.user
        elif hasattr(obj, 'course'):
            return obj.course.instructor == request.user
        elif hasattr(obj, 'module'):
            return obj.module.course.instructor == request.user
        
        return False


class IsEnrolledStudent(permissions.BasePermission):
    """
    Custom permission to only allow enrolled students to access course content.
    """
    
    def has_permission(self, request, view):
        return request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Teachers can always access their own content
        if request.user.is_teacher:
            if hasattr(obj, 'instructor'):
                return obj.instructor == request.user
            elif hasattr(obj, 'course'):
                return obj.course.instructor == request.user
            elif hasattr(obj, 'module'):
                return obj.module.course.instructor == request.user
        
        # Students need to be enrolled in the course
        course = None
        if hasattr(obj, 'course'):
            course = obj.course
        elif hasattr(obj, 'module'):
            course = obj.module.course
        elif hasattr(obj, 'lesson'):
            course = obj.lesson.module.course
        
        if course:
            return Enrollment.objects.filter(
                student=request.user,
                course=course,
                status=Enrollment.ACTIVE
            ).exists()
        
        return False


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions for any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only for the owner
        return obj.student == request.user or obj.instructor == request.user 
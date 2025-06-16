from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

class UserRole(models.TextChoices):
    STUDENT = 'STUDENT', _('Student')
    INSTRUCTOR = 'INSTRUCTOR', _('Instructor')
    ADMIN = 'ADMIN', _('Admin')

class User(AbstractUser):
    """
    Custom user model with role-based permissions
    """
    email = models.EmailField(_('email address'), unique=True)
    role = models.CharField(
        max_length=10,
        choices=UserRole.choices,
        default=UserRole.STUDENT,
    )
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    
    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def is_student(self):
        return self.role == UserRole.STUDENT
    
    @property
    def is_instructor(self):
        return self.role == UserRole.INSTRUCTOR
    
    @property
    def is_admin(self):
        return self.role == UserRole.ADMIN or self.is_superuser

    @property
    def courses_taught_count(self):
        return self.courses_teaching.count()

    @property
    def students_taught_count(self):
        from courses.models import Enrollment
        return Enrollment.objects.filter(course__in=self.courses_teaching.all()).values('student').distinct().count()

    @property
    def tasks_created_count(self):
        return sum(course.tasks.count() for course in self.courses_teaching.all())

    @property
    def exams_created_count(self):
        return sum(course.exams.count() for course in self.courses_teaching.all())

class UserProfile(models.Model):
    """
    Extended profile information for User
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    
    def __str__(self):
        return f"Profile for {self.user.email}"

class Notification(models.Model):
    """
    Model for user notifications
    """
    NOTIFICATION_TYPES = [
        ('COURSE', 'Course Update'),
        ('ASSIGNMENT', 'New Assignment'),
        ('GRADE', 'Grade Update'),
        ('SYSTEM', 'System Notification'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    link = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.user.email}"

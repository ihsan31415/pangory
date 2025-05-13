from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

class CourseStatus(models.TextChoices):
    DRAFT = 'DRAFT', _('Draft')
    PUBLISHED = 'PUBLISHED', _('Published')
    ARCHIVED = 'ARCHIVED', _('Archived')

class Course(models.Model):
    """
    Course model representing a learning course
    """
    title = models.CharField(max_length=255)
    description = models.TextField()
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='courses_teaching'
    )
    students = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='courses_enrolled',
        blank=True
    )
    thumbnail = models.ImageField(upload_to='course_thumbnails/', null=True, blank=True)
    status = models.CharField(
        max_length=10,
        choices=CourseStatus.choices,
        default=CourseStatus.DRAFT
    )
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title
    
    @property
    def is_published(self):
        return self.status == CourseStatus.PUBLISHED
    
    @property
    def student_count(self):
        return self.students.count()
    
    @property
    def module_count(self):
        return self.modules.count()

class Module(models.Model):
    """
    Module model representing a section of a course
    """
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"

class MaterialType(models.TextChoices):
    VIDEO = 'VIDEO', _('Video')
    PDF = 'PDF', _('PDF')
    TEXT = 'TEXT', _('Text')
    QUIZ_LINK = 'QUIZ_LINK', _('Quiz Link')

class Material(models.Model):
    """
    Material model representing learning content in a module
    """
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='materials')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    type = models.CharField(
        max_length=10,
        choices=MaterialType.choices,
        default=MaterialType.TEXT
    )
    content = models.TextField(blank=True)  # For TEXT type
    file = models.FileField(upload_to='course_materials/', null=True, blank=True)  # For PDF/VIDEO
    url = models.URLField(blank=True)  # For external resources
    order = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.module.title} - {self.title}"

class Task(models.Model):
    """
    Task model representing assignments for students
    """
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=255)
    description = models.TextField()
    due_date = models.DateTimeField(null=True, blank=True)
    points = models.PositiveIntegerField(default=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"

class TaskSubmission(models.Model):
    """
    Task submission model for student task responses
    """
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='task_submissions'
    )
    file = models.FileField(upload_to='task_submissions/', null=True, blank=True)
    content = models.TextField(blank=True)
    grade = models.FloatField(null=True, blank=True)
    feedback = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    graded_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['task', 'student']
    
    def __str__(self):
        return f"{self.student.email} - {self.task.title}"

class Enrollment(models.Model):
    """
    Enrollment model representing student enrollment in courses
    """
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='enrollments'
    )
    enrolled_at = models.DateTimeField(auto_now_add=True)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['course', 'student']
    
    def __str__(self):
        return f"{self.student.email} enrolled in {self.course.title}"

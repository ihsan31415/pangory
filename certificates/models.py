from django.db import models
from django.conf import settings
from courses.models import Course
from exams.models import ExamSession
import uuid

class Certificate(models.Model):
    """
    Certificate model for completed courses
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='certificates'
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='certificates')
    exam_session = models.OneToOneField(
        ExamSession, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='certificate'
    )
    issue_date = models.DateTimeField(auto_now_add=True)
    expiration_date = models.DateTimeField(null=True, blank=True)
    certificate_file = models.FileField(upload_to='certificates/', null=True, blank=True)
    
    class Meta:
        unique_together = ['user', 'course']
    
    def __str__(self):
        return f"Certificate for {self.user.email} - {self.course.title}"
    
    @property
    def is_valid(self):
        if self.expiration_date:
            from django.utils import timezone
            return timezone.now() < self.expiration_date
        return True
    
    @property
    def certificate_url(self):
        if self.certificate_file:
            return self.certificate_file.url
        return None
    
    def save(self, *args, **kwargs):
        # Generate certificate file if it doesn't exist
        super().save(*args, **kwargs)

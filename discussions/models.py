from django.db import models
from django.conf import settings
from courses.models import Course

class DiscussionPost(models.Model):
    """
    Discussion post model for course forums
    """
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='discussion_posts')
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='discussion_posts'
    )
    topic = models.CharField(max_length=255)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.course.title} - {self.topic}"
    
    @property
    def reply_count(self):
        return self.replies.count()

class DiscussionReply(models.Model):
    """
    Reply model for discussion posts
    """
    post = models.ForeignKey(DiscussionPost, on_delete=models.CASCADE, related_name='replies')
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='discussion_replies'
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
        verbose_name_plural = 'Discussion replies'
    
    def __str__(self):
        return f"Reply to {self.post.topic} by {self.author.email}"

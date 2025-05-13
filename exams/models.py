from django.db import models
from django.conf import settings
from courses.models import Course

class QuestionType(models.TextChoices):
    MULTIPLE_CHOICE = 'MULTIPLE_CHOICE', 'Multiple Choice'
    ESSAY = 'ESSAY', 'Essay'

class Exam(models.Model):
    """
    Exam model for course assessments
    """
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='exams')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    duration_minutes = models.PositiveIntegerField(default=60)
    passing_score = models.PositiveIntegerField(default=70)  # Percentage
    available_from = models.DateTimeField(null=True, blank=True)
    available_until = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"
    
    @property
    def total_points(self):
        return sum(question.points for question in self.questions.all())
    
    @property
    def question_count(self):
        return self.questions.count()

class Question(models.Model):
    """
    Question model for exams
    """
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    type = models.CharField(
        max_length=20,
        choices=QuestionType.choices,
        default=QuestionType.MULTIPLE_CHOICE
    )
    points = models.PositiveIntegerField(default=10)
    order = models.PositiveIntegerField(default=1)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"Question {self.order} in {self.exam.title}"

class QuestionOption(models.Model):
    """
    Option model for multiple choice questions
    """
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=1)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"Option for {self.question}"

class ExamSessionStatus(models.TextChoices):
    STARTED = 'STARTED', 'Started'
    IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
    SUBMITTED = 'SUBMITTED', 'Submitted'
    GRADED = 'GRADED', 'Graded'

class ExamSession(models.Model):
    """
    Exam session model for tracking student exam attempts
    """
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='sessions')
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='exam_sessions'
    )
    status = models.CharField(
        max_length=15,
        choices=ExamSessionStatus.choices,
        default=ExamSessionStatus.STARTED
    )
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    score = models.FloatField(null=True, blank=True)
    passed = models.BooleanField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.student.email} - {self.exam.title}"
    
    @property
    def is_completed(self):
        return self.status in [ExamSessionStatus.SUBMITTED, ExamSessionStatus.GRADED]
    
    @property
    def time_elapsed(self):
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds() / 60
        return None

class Answer(models.Model):
    """
    Answer model for storing student responses to questions
    """
    exam_session = models.ForeignKey(ExamSession, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='student_answers')
    selected_option = models.ForeignKey(
        QuestionOption, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='selected_in_answers'
    )
    text_answer = models.TextField(blank=True)  # For essay questions
    points_earned = models.FloatField(null=True, blank=True)
    feedback = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['exam_session', 'question']
    
    def __str__(self):
        return f"Answer to {self.question} by {self.exam_session.student.email}"

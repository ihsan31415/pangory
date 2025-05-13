from django.contrib import admin
from .models import Exam, Question, QuestionOption, ExamSession, Answer

class QuestionOptionInline(admin.TabularInline):
    model = QuestionOption
    extra = 0

class QuestionInline(admin.TabularInline):
    model = Question
    extra = 0
    show_change_link = True

class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0
    readonly_fields = ('question', 'selected_option', 'text_answer')

@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'duration_minutes', 'passing_score', 'question_count', 'total_points')
    list_filter = ('course', 'created_at')
    search_fields = ('title', 'description', 'course__title')
    inlines = [QuestionInline]

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'exam', 'type', 'points', 'order')
    list_filter = ('exam', 'type')
    search_fields = ('text', 'exam__title')
    inlines = [QuestionOptionInline]

@admin.register(QuestionOption)
class QuestionOptionAdmin(admin.ModelAdmin):
    list_display = ('text', 'question', 'is_correct', 'order')
    list_filter = ('question__exam', 'is_correct')
    search_fields = ('text', 'question__text')

@admin.register(ExamSession)
class ExamSessionAdmin(admin.ModelAdmin):
    list_display = ('exam', 'student', 'status', 'score', 'passed', 'start_time', 'end_time')
    list_filter = ('exam', 'status', 'passed')
    search_fields = ('exam__title', 'student__email')
    readonly_fields = ('start_time',)
    inlines = [AnswerInline]

@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('question', 'exam_session', 'points_earned')
    list_filter = ('exam_session__exam', 'exam_session__student')
    search_fields = ('question__text', 'text_answer', 'exam_session__student__email')
    readonly_fields = ('exam_session', 'question')

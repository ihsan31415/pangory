from django.contrib import admin
from .models import Course, Module, Material, Task, TaskSubmission, Enrollment

class ModuleInline(admin.TabularInline):
    model = Module
    extra = 0

class MaterialInline(admin.TabularInline):
    model = Material
    extra = 0

class TaskInline(admin.TabularInline):
    model = Task
    extra = 0

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'instructor', 'status', 'price', 'student_count', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('title', 'description', 'instructor__email')
    inlines = [ModuleInline, TaskInline]
    filter_horizontal = ('students',)

@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order', 'created_at')
    list_filter = ('course',)
    search_fields = ('title', 'description', 'course__title')
    inlines = [MaterialInline]

@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ('title', 'module', 'type', 'order')
    list_filter = ('type', 'module__course')
    search_fields = ('title', 'description')

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'due_date', 'points')
    list_filter = ('course', 'due_date')
    search_fields = ('title', 'description')

@admin.register(TaskSubmission)
class TaskSubmissionAdmin(admin.ModelAdmin):
    list_display = ('task', 'student', 'grade', 'submitted_at', 'graded_at')
    list_filter = ('task__course', 'submitted_at', 'graded_at')
    search_fields = ('task__title', 'student__email', 'content')

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'enrolled_at', 'completed')
    list_filter = ('course', 'enrolled_at', 'completed')
    search_fields = ('student__email', 'course__title')

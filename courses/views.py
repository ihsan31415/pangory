from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Course, Enrollment, Module, Task, TaskSubmission
from django.contrib.admin.views.decorators import staff_member_required
from .forms import CourseForm 
from django.http import HttpResponseForbidden

def student_course_list(request):
    all_courses = Course.objects.filter(status='PUBLISHED')
    if request.user.is_authenticated:
        enrolled_ids = Enrollment.objects.filter(student=request.user).values_list('course_id', flat=True)
        my_courses = all_courses.filter(id__in=enrolled_ids)
        available_courses = all_courses.exclude(id__in=enrolled_ids)
        for course in available_courses:
            course.is_enrolled = False
        for course in my_courses:
            course.is_enrolled = True
    else:
        available_courses = all_courses
        my_courses = []
        for course in available_courses:
            course.is_enrolled = False
    return render(request, 'layout/student_course_list.html', {
        'available_courses': available_courses,
        'my_courses': my_courses,
    })

@login_required
def enroll_course(request, course_id):
    course = get_object_or_404(Course, id=course_id, status='PUBLISHED')  # perbaiki status
    Enrollment.objects.get_or_create(student=request.user, course=course)
    return redirect('my_courses')

@login_required
def my_courses(request):
    # Ambil semua course yang sudah di-enroll user
    enrolled_ids = Enrollment.objects.filter(student=request.user).values_list('course_id', flat=True)
    my_courses = Course.objects.filter(id__in=enrolled_ids, status='PUBLISHED')
    for course in my_courses:
        course.is_enrolled = True
    return render(request, 'courses/my_courses.html', {'my_courses': my_courses})

@login_required
def course_detail(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    modules = course.modules.all()
    tasks = course.tasks.all()
    student_count = course.students.count()
    module_count = modules.count()
    return render(request, 'courses/course_detail.html', {
        'course': course,
        'modules': modules,
        'tasks': tasks,
        'student_count': student_count,
        'module_count': module_count,
    })

@login_required
def course_enrolled_students(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    enrollments = course.enrollments.select_related('student')
    students = [enrollment.student for enrollment in enrollments]
    return render(request, 'courses/course_enrolled_students.html', {
        'course': course,
        'students': students,
    })

@login_required
def task_detail(request, course_id, task_id):
    course = get_object_or_404(Course, id=course_id)
    task = get_object_or_404(Task, id=task_id, course=course)
    # Cek apakah user sudah enroll
    if not Enrollment.objects.filter(student=request.user, course=course).exists():
        return HttpResponseForbidden("Anda belum terdaftar di kursus ini.")
    # Cek submission
    submission = TaskSubmission.objects.filter(task=task, student=request.user).first()
    if request.method == 'POST':
        answer_text = request.POST.get('answer_text', '')
        answer_file = request.FILES.get('answer_file')
        if submission:
            submission.answer_text = answer_text
            if answer_file:
                submission.answer_file = answer_file
            submission.save()
        else:
            submission = TaskSubmission.objects.create(
                task=task,
                student=request.user,
                answer_text=answer_text,
                answer_file=answer_file
            )
        return redirect('task_detail', course_id=course.id, task_id=task.id)
    return render(request, 'courses/task_detail.html', {
        'course': course,
        'task': task,
        'submission': submission,
    })

@staff_member_required
def admin_course_list(request):
    courses = Course.objects.all()
    return render(request, 'courses/admin_course_list.html', {'courses': courses})

@staff_member_required
def admin_course_add(request):
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('admin_course_list')
    else:
        form = CourseForm()
    return render(request, 'courses/admin_course_form.html', {'form': form, 'action': 'Tambah'})

@staff_member_required
def admin_course_edit(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            return redirect('admin_course_list')
    else:
        form = CourseForm(instance=course)
    return render(request, 'courses/admin_course_form.html', {'form': form, 'action': 'Edit'})

@staff_member_required
def admin_course_delete(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if request.method == 'POST':
        course.delete()
        return redirect('admin_course_list')
    return render(request, 'courses/admin_course_confirm_delete.html', {'course': course})



@login_required
def instructor_course_list(request):
    # Hanya course yang diajar oleh instructor ini
    courses = Course.objects.filter(instructor=request.user)
    return render(request, 'courses/instructor_course_list.html', {'courses': courses})

@login_required
def instructor_course_add(request):
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save(commit=False)
            course.instructor = request.user  # Set instructor ke user yang login
            course.save()
            return redirect('instructor_course_list')
    else:
        form = CourseForm()
    return render(request, 'courses/instructor_course_form.html', {'form': form, 'action': 'Tambah'})

@login_required
def instructor_course_edit(request, course_id):
    course = get_object_or_404(Course, id=course_id, instructor=request.user)
    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            return redirect('instructor_course_list')
    else:
        form = CourseForm(instance=course)
    return render(request, 'courses/instructor_course_form.html', {'form': form, 'action': 'Edit'})

@login_required
def instructor_course_delete(request, course_id):
    course = get_object_or_404(Course, id=course_id, instructor=request.user)
    if request.method == 'POST':
        course.delete()
        return redirect('instructor_course_list')
    return render(request, 'courses/instructor_course_confirm_delete.html', {'course': course})
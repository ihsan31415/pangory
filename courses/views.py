from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Course, Enrollment
from django.contrib.admin.views.decorators import staff_member_required
from .forms import CourseForm 

@login_required
def student_course_list(request):
    # Semua course yang published
    all_courses = Course.objects.filter(status='PUBLISHED')
    # Course yang sudah di-enroll user
    enrolled_ids = Enrollment.objects.filter(student=request.user).values_list('course_id', flat=True)
    my_courses = all_courses.filter(id__in=enrolled_ids)
    available_courses = all_courses.exclude(id__in=enrolled_ids)
    for course in available_courses:
        course.is_enrolled = False
    for course in my_courses:
        course.is_enrolled = True
    return render(request, 'courses/student_course_list.html', {
        'available_courses': available_courses,
        'my_courses': my_courses,
    })

@login_required
def enroll_course(request, course_id):
    course = get_object_or_404(Course, id=course_id, status='published')
    Enrollment.objects.get_or_create(user=request.user, course=course)
    return redirect('my_courses')

@login_required
def my_courses(request):
    enrollments = Enrollment.objects.filter(user=request.user).select_related('course')
    return render(request, 'courses/my_courses.html', {'enrollments': enrollments})

@login_required
def course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    # Pastikan user sudah enroll
    if not Enrollment.objects.filter(student=request.user, course=course).exists():
        return redirect('student_course_list')
    modules = course.modules.all().order_by('order')
    tasks = course.tasks.all()
    return render(request, 'courses/course_detail.html', {
        'course': course,
        'modules': modules,
        'tasks': tasks,
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
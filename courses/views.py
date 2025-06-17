from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Course, Enrollment, Module, Task, TaskSubmission, Material
from django.contrib.admin.views.decorators import staff_member_required
from .forms import CourseForm, MaterialForm
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
    course = get_object_or_404(Course, id=course_id, status='PUBLISHED')
    enrollment, created = Enrollment.objects.get_or_create(student=request.user, course=course)
    course.students.add(request.user)  # Pastikan user juga masuk ke field students
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
    # Hitung apakah ada video youtube di materi
    has_video = any(
        material.type == 'VIDEO' and material.url and (
            'youtube.com' in material.url or 'youtu.be' in material.url
        )
        for module in modules
        for material in module.materials.all()
    )
    return render(request, 'courses/course_detail.html', {
        'course': course,
        'modules': modules,
        'tasks': tasks,
        'student_count': student_count,
        'module_count': module_count,
        'has_video': has_video,
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

@login_required
def course_player(request, course_id, material_id):
    course = get_object_or_404(Course, pk=course_id)
    material = get_object_or_404(Material, pk=material_id)
    module = material.module
    # Only allow enrolled students or instructor
    if not (course.students.filter(id=request.user.id).exists() or course.instructor.id == request.user.id or request.user.is_staff or request.user.is_superuser):
        return HttpResponseForbidden("Anda tidak terdaftar di kursus ini.")
    # Get all materials in this module, ordered
    materials = list(module.materials.all())
    # Find current, previous, and next material
    current_idx = next((i for i, m in enumerate(materials) if m.id == material.id), None)
    prev_material = materials[current_idx - 1] if current_idx is not None and current_idx > 0 else None
    next_material = materials[current_idx + 1] if current_idx is not None and current_idx < len(materials) - 1 else None
    return render(request, 'courses/player.html', {
        'course': course,
        'material': material,
        'materials': materials,
        'prev_material': prev_material,
        'next_material': next_material,
    })

@login_required
def course_modules(request, course_id):
    course = get_object_or_404(Course, id=course_id, instructor=request.user)
    modules = course.modules.all().order_by('order')
    return render(request, 'courses/course_modules.html', {
        'course': course,
        'modules': modules,
    })

@login_required
def course_tasks(request, course_id):
    course = get_object_or_404(Course, id=course_id, instructor=request.user)
    tasks = course.tasks.all().order_by('due_date')
    return render(request, 'courses/course_tasks.html', {
        'course': course,
        'tasks': tasks,
    })

@login_required
def course_enrollments(request, course_id):
    course = get_object_or_404(Course, id=course_id, instructor=request.user)
    enrollments = course.enrollments.select_related('student').all()
    return render(request, 'courses/course_enrollments.html', {
        'course': course,
        'enrollments': enrollments,
    })

@login_required
def add_module(request, course_id):
    course = get_object_or_404(Course, id=course_id, instructor=request.user)
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        order = request.POST.get('order')
        module = Module.objects.create(
            course=course,
            title=title,
            description=description,
            order=order
        )
        return redirect('course_modules', course_id=course.id)
    return render(request, 'courses/module_form.html', {
        'course': course,
        'action': 'Tambah',
    })

@login_required
def edit_module(request, course_id, module_id):
    course = get_object_or_404(Course, id=course_id, instructor=request.user)
    module = get_object_or_404(Module, id=module_id, course=course)
    if request.method == 'POST':
        module.title = request.POST.get('title')
        module.description = request.POST.get('description')
        module.order = request.POST.get('order')
        module.save()
        return redirect('course_modules', course_id=course.id)
    return render(request, 'courses/module_form.html', {
        'course': course,
        'module': module,
        'action': 'Edit',
    })

@login_required
def delete_module(request, course_id, module_id):
    course = get_object_or_404(Course, id=course_id, instructor=request.user)
    module = get_object_or_404(Module, id=module_id, course=course)
    if request.method == 'POST':
        module.delete()
        return redirect('course_modules', course_id=course.id)
    return render(request, 'courses/module_confirm_delete.html', {
        'course': course,
        'module': module,
    })

@login_required
def add_task(request, course_id):
    course = get_object_or_404(Course, id=course_id, instructor=request.user)
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        due_date = request.POST.get('due_date')
        task = Task.objects.create(
            course=course,
            title=title,
            description=description,
            due_date=due_date
        )
        return redirect('course_tasks', course_id=course.id)
    return render(request, 'courses/task_form.html', {
        'course': course,
        'action': 'Tambah',
    })

@login_required
def edit_task(request, course_id, task_id):
    course = get_object_or_404(Course, id=course_id, instructor=request.user)
    task = get_object_or_404(Task, id=task_id, course=course)
    if request.method == 'POST':
        task.title = request.POST.get('title')
        task.description = request.POST.get('description')
        task.due_date = request.POST.get('due_date')
        task.save()
        return redirect('course_tasks', course_id=course.id)
    return render(request, 'courses/task_form.html', {
        'course': course,
        'task': task,
        'action': 'Edit',
    })

@login_required
def delete_task(request, course_id, task_id):
    course = get_object_or_404(Course, id=course_id, instructor=request.user)
    task = get_object_or_404(Task, id=task_id, course=course)
    if request.method == 'POST':
        task.delete()
        return redirect('course_tasks', course_id=course.id)
    return render(request, 'courses/task_confirm_delete.html', {
        'course': course,
        'task': task,
    })

@login_required
def add_material(request, module_id):
    module = get_object_or_404(Module, id=module_id)
    course = module.course
    if request.user != course.instructor and not request.user.is_staff:
        return HttpResponseForbidden("Anda tidak berhak menambah materi pada modul ini.")
    if request.method == 'POST':
        form = MaterialForm(request.POST, request.FILES)
        if form.is_valid():
            material = form.save(commit=False)
            material.module = module
            material.save()
            return redirect('course_detail', course_id=course.id)
    else:
        form = MaterialForm()
    return render(request, 'courses/material_form.html', {'form': form, 'module': module, 'course': course, 'action': 'Tambah'})

@login_required
def edit_material(request, module_id, material_id):
    module = get_object_or_404(Module, id=module_id)
    material = get_object_or_404(Material, id=material_id, module=module)
    course = module.course
    if request.user != course.instructor and not request.user.is_staff:
        return HttpResponseForbidden("Anda tidak berhak mengedit materi pada modul ini.")
    if request.method == 'POST':
        form = MaterialForm(request.POST, request.FILES, instance=material)
        if form.is_valid():
            form.save()
            return redirect('course_detail', course_id=course.id)
    else:
        form = MaterialForm(instance=material)
    return render(request, 'courses/material_form.html', {'form': form, 'module': module, 'course': course, 'action': 'Edit'})

@login_required
def unenroll_course(request, course_id):
    course = get_object_or_404(Course, id=course_id, status='PUBLISHED')
    enrollment = Enrollment.objects.filter(student=request.user, course=course).first()
    if request.method == 'POST':
        if enrollment:
            enrollment.delete()
        course.students.remove(request.user)
        return redirect('my_courses')
    return render(request, 'courses/unenroll_course_confirm.html', {'course': course})
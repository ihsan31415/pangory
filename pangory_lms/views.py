from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from courses.models import Course, Enrollment
from certificates.models import Certificate

def index(request):
    return render(request, 'layout/index.html')

def about(request):
    return render(request, 'layout/about.html')

def contact_view(request):
    return render(request, 'layout/contact.html')

def student_dashboard(request):
    return render(request, 'account/student_dashboard.html')


@login_required
def student_dashboard(request):
    user = request.user
    # Kursus yang diikuti
    enrolled_ids = Enrollment.objects.filter(student=user).values_list('course_id', flat=True)
    my_courses = Course.objects.filter(id__in=enrolled_ids, status='PUBLISHED')
    # Dummy progress: rata-rata 100% jika sudah ada, atau 0%
    if my_courses.exists():
        progress_percent = 50  # Ganti dengan logika progres sebenarnya jika ada
    else:
        progress_percent = 0
    # Sertifikat user
    certificates = Certificate.objects.filter(user=user)
    # Dummy notifikasi
    notifications = [
        {"message": "Selamat datang di Pangory!", "timestamp": user.date_joined},
        # Tambahkan notifikasi lain sesuai kebutuhan
    ]
    return render(request, 'account/student_dashboard.html', {
        'my_courses': my_courses,
        'progress_percent': progress_percent,
        'certificates': certificates,
        'notifications': notifications,
    })
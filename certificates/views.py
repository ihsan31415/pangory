from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from certificates.models import Certificate
from courses.models import Course, Enrollment
from django.http import FileResponse, Http404
import os
from django.conf import settings

@login_required
def certificate_list(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    certificates = Certificate.objects.filter(user=request.user, course=course)
    return render(request, 'certificates/certificate_list.html', {
        'course': course,
        'certificates': certificates,
    })

@login_required
def certificate_detail(request, course_id, certificate_id):
    course = get_object_or_404(Course, id=course_id)
    certificate = get_object_or_404(Certificate, id=certificate_id, user=request.user, course=course)
    return render(request, 'certificates/certificate_detail.html', {
        'course': course,
        'certificate': certificate,
    })

@login_required
def certificate_download(request, course_id, certificate_id):
    certificate = get_object_or_404(Certificate, id=certificate_id, user=request.user, course_id=course_id)
    if not certificate.certificate_file:
        raise Http404("Certificate file not found.")
    file_path = certificate.certificate_file.path
    if not os.path.exists(file_path):
        raise Http404("Certificate file not found.")
    response = FileResponse(open(file_path, 'rb'), as_attachment=True, filename=os.path.basename(file_path))
    return response
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from .models import DiscussionPost, DiscussionReply
from courses.models import Course

@login_required
def course_discussion(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    user = request.user
    # Hanya yang enroll atau instruktur/staff
    if not (course.students.filter(id=user.id).exists() or course.instructor.id == user.id or user.is_staff or user.is_superuser):
        raise PermissionDenied("Anda tidak terdaftar di kursus ini.")
    posts = DiscussionPost.objects.filter(course=course).order_by('-created_at')
    return render(request, 'discuss/course_discussion.html', {'course': course, 'posts': posts})

@login_required
def discussion_post_detail(request, course_id, post_id):
    course = get_object_or_404(Course, pk=course_id)
    post = get_object_or_404(DiscussionPost, pk=post_id, course=course)
    user = request.user
    if not (course.students.filter(id=user.id).exists() or course.instructor.id == user.id or user.is_staff or user.is_superuser):
        raise PermissionDenied("Anda tidak terdaftar di kursus ini.")
    replies = DiscussionReply.objects.filter(post=post).order_by('created_at')
    return render(request, 'discuss/discussion_post_detail.html', {'course': course, 'post': post, 'replies': replies})

@login_required
def create_discussion_post(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    user = request.user
    if not (course.students.filter(id=user.id).exists() or course.instructor.id == user.id or user.is_staff or user.is_superuser):
        raise PermissionDenied("Anda tidak terdaftar di kursus ini.")
    if request.method == 'POST':
        topic = request.POST.get('topic')
        content = request.POST.get('content')
        if topic and content:
            post = DiscussionPost.objects.create(course=course, author=user, topic=topic, content=content)
            return redirect('discussion_post_detail', course_id=course.id, post_id=post.id)
    return render(request, 'discuss/create_discussion_post.html', {'course': course})

@login_required
def reply_to_discussion_post(request, course_id, post_id):
    course = get_object_or_404(Course, pk=course_id)
    post = get_object_or_404(DiscussionPost, pk=post_id, course=course)
    user = request.user
    if not (course.students.filter(id=user.id).exists() or course.instructor.id == user.id or user.is_staff or user.is_superuser):
        raise PermissionDenied("Anda tidak terdaftar di kursus ini.")
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            DiscussionReply.objects.create(post=post, author=user, content=content)
            return redirect('discussion_post_detail', course_id=course.id, post_id=post.id)
    return render(request, 'discuss/reply_to_discussion_post.html', {'course': course, 'post': post})
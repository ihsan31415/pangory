"""
URL configuration for pangory_lms project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from graphene_django.views import GraphQLView
from django.views.decorators.csrf import csrf_exempt
from . import views
from accounts import views as accounts_views
from django.contrib.auth.views import LogoutView
from courses import views as courses_views
from discussions import views as discussions_views
from exams import views as exams_views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('graphql/', csrf_exempt(GraphQLView.as_view(graphiql=True))),
    path('register/', accounts_views.register, name='register'),
    path('login/', accounts_views.login_view, name='login'),
    path('userprofile/', accounts_views.user_profile, name='user_profile'),
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact_view, name='contact'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    # student
    path('courses/', courses_views.student_course_list, name='student_course_list'),
    path('courses/enroll/<int:course_id>/', courses_views.enroll_course, name='enroll_course'),
    path('courses/my/', courses_views.my_courses, name='my_courses'),
    path('courses/<int:course_id>/', courses_views.course_detail, name='course_detail'),
    path('courses/<int:course_id>/students/', courses_views.course_enrolled_students, name='course_enrolled_students'),
    path('courses/<int:course_id>/task/<int:task_id>/', courses_views.task_detail, name='task_detail'),
    # untuk discsission
    path('courses/<int:course_id>/discussion/', discussions_views.course_discussion, name='course_discussion'),
    path('courses/<int:course_id>/discussion/post/<int:post_id>/', discussions_views.discussion_post_detail, name='discussion_post_detail'),
    path('courses/<int:course_id>/discussion/new/', discussions_views.create_discussion_post, name='create_discussion_post'),
    path('courses/<int:course_id>/discussion/post/<int:post_id>/reply/', discussions_views.reply_to_discussion_post, name='reply_to_discussion_post'),
    # exam
    path('courses/<int:course_id>/exams/', exams_views.exam_list, name='exam_list'),
    path('courses/<int:course_id>/exams/<int:exam_id>/', exams_views.exam_detail, name='exam_detail'),
    path('courses/<int:course_id>/exams/<int:exam_id>/start/', exams_views.start_exam, name='start_exam'),
    path('courses/<int:course_id>/exams/session/<int:session_id>/', exams_views.exam_session, name='exam_session'),
    path('courses/<int:course_id>/exams/session/<int:session_id>/submit/', exams_views.submit_answer, name='submit_answer'),

    path('dashboard/', views.student_dashboard, name='student_dashboard'),
    # path('admin/courses/', courses_views.admin_course_list, name='admin_course_list'),
    # path('admin/courses/add/', courses_views.admin_course_add, name='admin_course_add'),
    # path('admin/courses/<int:course_id>/edit/', courses_views.admin_course_edit, name='admin_course_edit'),
    # path('admin/courses/<int:course_id>/delete/', courses_views.admin_course_delete, name='admin_course_delete'),
    # path('instructor/courses/', courses_views.instructor_course_list, name='instructor_course_list'),
    # path('instructor/courses/add/', courses_views.instructor_course_add, name='instructor_course_add'),
    # path('instructor/courses/<int:course_id>/edit/', courses_views.instructor_course_edit, name='instructor_course_edit'),
    # path('instructor/courses/<int:course_id>/delete/', courses_views.instructor_course_delete, name='instructor_course_delete'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

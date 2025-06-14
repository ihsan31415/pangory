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


urlpatterns = [
    path('admin/', admin.site.urls),
    path('graphql/', csrf_exempt(GraphQLView.as_view(graphiql=True))),
    path('register/', accounts_views.register, name='register'),
    path('login/', accounts_views.login_view, name='login'),
    path('userprofile/', accounts_views.user_profile, name='user_profile'),
    path('', views.index, name='index'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('courses/', courses_views.student_course_list, name='student_course_list'),
    path('courses/enroll/<int:course_id>/', courses_views.enroll_course, name='enroll_course'),
    path('courses/my/', courses_views.my_courses, name='my_courses'),
    path('courses/<int:course_id>/', courses_views.course_detail, name='course_detail'),
    path('admin/courses/', courses_views.admin_course_list, name='admin_course_list'),
    path('admin/courses/add/', courses_views.admin_course_add, name='admin_course_add'),
    path('admin/courses/<int:course_id>/edit/', courses_views.admin_course_edit, name='admin_course_edit'),
    path('admin/courses/<int:course_id>/delete/', courses_views.admin_course_delete, name='admin_course_delete'),
    path('instructor/courses/', courses_views.instructor_course_list, name='instructor_course_list'),
    path('instructor/courses/add/', courses_views.instructor_course_add, name='instructor_course_add'),
    path('instructor/courses/<int:course_id>/edit/', courses_views.instructor_course_edit, name='instructor_course_edit'),
    path('instructor/courses/<int:course_id>/delete/', courses_views.instructor_course_delete, name='instructor_course_delete'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

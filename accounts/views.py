from django.shortcuts import render, redirect
from django.contrib import messages
from .models import User
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from courses.models import Course, Enrollment, TaskSubmission
from certificates.models import Certificate
from django.contrib.auth import authenticate, login

def register(request):
    if request.method == 'POST':
        email = request.POST['email']
        username = request.POST['username']
        password = request.POST['password']
        role = request.POST['role'].upper()
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email sudah digunakan.")
            return render(request, 'auth/register.html')
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username sudah digunakan.")
            return render(request, 'auth/register.html')
        user = User.objects.create_user(
            email=email,
            username=username,
            password=password,
            role=role
        )
        messages.success(request, "Registrasi berhasil! Silakan login.")
        return redirect('login')
    return render(request, 'auth/register.html')

def login_view(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        
        # Debug info
        print(f"Login attempt with email: {email}")
        
        # Coba autentikasi dengan email
        user = authenticate(request, email=email, password=password)
        
        if user is not None:
            print(f"Authentication successful for {email}, is_admin: {user.is_admin}, is_superuser: {user.is_superuser}")
            login(request, user)
            
            # Redirect berdasarkan role
            if user.is_admin or user.is_superuser:
                print(f"Redirecting admin user to custom admin dashboard")
                return redirect('admin_dashboard')  # Redirect ke admin dashboard kustom
            else:
                print(f"Redirecting regular user to profile")
                return redirect('user_profile')
        else:
            print(f"Authentication failed for {email}")
            messages.error(request, "Email atau password salah.")
            
    return render(request, 'auth/login.html')

@login_required
def user_profile(request):
    user = request.user
    profile = user.profile
    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)

        profile.bio = request.POST.get('bio', profile.bio)
        profile.address = request.POST.get('address', profile.address)
        profile.phone_number = request.POST.get('phone', profile.phone_number)
        profile.date_of_birth = request.POST.get('dob', profile.date_of_birth)

        # Jika ingin update password:
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        if current_password and new_password:
            if user.check_password(current_password):
                user.set_password(new_password)
            else:
                messages.error(request, "Password saat ini salah.")
                return render(request, 'account/userprofile.html', {'user': user})

        # Debug Avatar Upload
        print("FILES:", request.FILES)
        if 'avatar' in request.FILES:
            try:
                avatar_file = request.FILES['avatar']
                print(f"Avatar received: {avatar_file.name}, size: {avatar_file.size}, content_type: {avatar_file.content_type}")
                profile.avatar = avatar_file
                print("Avatar assigned to profile")
            except Exception as e:
                print(f"Error saving avatar: {e}")
        else:
            print("No avatar file in request.FILES")

        try:
            user.save()
            profile.save()
            print("User and profile saved successfully")
            if profile.avatar:
                print(f"Avatar path: {profile.avatar.path}, URL: {profile.avatar.url}")
        except Exception as e:
            print(f"Error saving user/profile: {e}")
            messages.error(request, f"Error saving profile: {e}")
            return render(request, 'account/userprofile.html', {'user': user})

        messages.success(request, "Profil berhasil diperbarui.")
        return redirect('user_profile')
    
    return render(request, 'account/userprofile.html', {'user': user})

@login_required
def statistics(request):
    user = request.user
    
    # Calculate completed tasks count (tasks that have been graded)
    completed_tasks_count = TaskSubmission.objects.filter(
        student=user,
        grade__isnull=False
    ).count()
    
    context = {
        'completed_tasks_count': completed_tasks_count,
    }
    
    return render(request, 'account/statistics.html', context)

@login_required
def admin_dashboard(request):
    # Periksa apakah pengguna adalah admin
    if not request.user.is_admin and not request.user.is_superuser:
        messages.error(request, "Anda tidak memiliki akses ke halaman ini.")
        return redirect('index')
    
    # Statistik untuk dashboard admin
    total_users = User.objects.count()
    total_students = User.objects.filter(role='STUDENT').count()
    total_instructors = User.objects.filter(role='INSTRUCTOR').count()
    
    # Statistik kursus
    from courses.models import Course
    total_courses = Course.objects.count()
    published_courses = Course.objects.filter(status='PUBLISHED').count()
    
    # Data untuk tabel
    user_list = User.objects.all().order_by('-date_joined')[:10]
    course_list = Course.objects.all().order_by('-created_at')[:10]
    
    context = {
        'total_users': total_users,
        'total_students': total_students,
        'total_instructors': total_instructors,
        'total_courses': total_courses,
        'published_courses': published_courses,
        'user_list': user_list,
        'course_list': course_list,
    }
    
    return render(request, 'admin/custom_admin_dashboard.html', context)
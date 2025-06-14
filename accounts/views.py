from django.shortcuts import render, redirect
from django.contrib import messages
from .models import User
from django.contrib.auth.decorators import login_required

def register(request):
    if request.method == 'POST':
        email = request.POST['email']
        username = request.POST['username']
        password = request.POST['password']
        role = request.POST['role'].upper()
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email sudah digunakan.")
            return render(request, 'register.html')
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username sudah digunakan.")
            return render(request, 'register.html')
        user = User.objects.create_user(
            email=email,
            username=username,
            password=password,
            role=role
        )
        messages.success(request, "Registrasi berhasil! Silakan login.")
        return redirect('login')
    return render(request, 'register.html')

from django.contrib.auth import authenticate, login

def login_view(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            return redirect('user_profile') 
        else:
            messages.error(request, "Email atau password salah.")
    return render(request, 'login.html')

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
                return render(request, 'userprofile.html', {'user': user})
        user.save()
        profile.save()

        messages.success(request, "Profil berhasil diperbarui.")

        return redirect('user_profile')
    return render(request, 'userprofile.html', {'user': user})
from django.shortcuts import render

def index(request):
    return render(request, 'index.html')

def about(request):
    return render(request, 'about.html')

def contact_view(request):
    return render(request, 'contact.html')

def student_dashboard(request):
    return render(request, 'student_dashboard.html')
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from exams.models import Exam, ExamSession, Question, QuestionOption, Answer, ExamSessionStatus, QuestionType
from courses.models import Course, Enrollment
from django.urls import reverse
from django import forms
from django.http import HttpResponseForbidden
from django.forms import ModelForm, inlineformset_factory
from django.utils import timezone
from django.contrib import messages

@login_required
def exam_list(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    # Hanya siswa yang harus enroll, instruktur/staff/superuser boleh akses
    if request.user != course.instructor and not request.user.is_staff and not request.user.is_superuser:
        if not Enrollment.objects.filter(student=request.user, course=course).exists():
            return render(request, 'exam/not_enrolled.html', {'course': course})
    exams = Exam.objects.filter(course=course)
    return render(request, 'exam/exam_list.html', {'course': course, 'exams': exams})

@login_required
def exam_detail(request, course_id, exam_id):
    course = get_object_or_404(Course, id=course_id)
    exam = get_object_or_404(Exam, id=exam_id, course=course)
    # Hanya siswa yang harus enroll, instruktur/staff/superuser boleh akses
    if request.user != course.instructor and not request.user.is_staff and not request.user.is_superuser:
        if not Enrollment.objects.filter(student=request.user, course=course).exists():
            return render(request, 'exam/not_enrolled.html', {'course': course})
    # Cek session aktif
    session = None
    completed_session = None
    if not (request.user == course.instructor or request.user.is_staff or request.user.is_superuser):
        session = ExamSession.objects.filter(exam=exam, student=request.user, status__in=[ExamSessionStatus.STARTED, ExamSessionStatus.IN_PROGRESS]).first()
        completed_session = ExamSession.objects.filter(exam=exam, student=request.user, status__in=[ExamSessionStatus.SUBMITTED, ExamSessionStatus.GRADED]).first()
    return render(request, 'exam/exam_detail.html', {
        'course': course,
        'exam': exam,
        'session': session,
        'completed_session': completed_session,
    })

@login_required
def start_exam(request, course_id, exam_id):
    course = get_object_or_404(Course, id=course_id)
    exam = get_object_or_404(Exam, id=exam_id, course=course)
    if not Enrollment.objects.filter(student=request.user, course=course).exists():
        return render(request, 'exam/not_enrolled.html', {'course': course})
    # Cek session aktif
    session, created = ExamSession.objects.get_or_create(
        exam=exam,
        student=request.user,
        status__in=[ExamSessionStatus.STARTED, ExamSessionStatus.IN_PROGRESS],
        defaults={'status': ExamSessionStatus.STARTED}
    )
    return redirect('exam_session', course_id=course.id, session_id=session.id)

@login_required
def exam_session(request, course_id, session_id):
    session = get_object_or_404(ExamSession, id=session_id, student=request.user)
    exam = session.exam
    questions = list(exam.questions.all())
    
    # Cek apakah ada soal
    if not questions:
        return render(request, 'exam/error.html', {
            'message': 'Ujian ini belum memiliki soal. Silakan hubungi instruktur.',
            'course': exam.course,
            'exam': exam
        })
        
    answers = {a.question_id: a for a in Answer.objects.filter(exam_session=session)}
    current_q = request.GET.get('q')
    if current_q:
        current_q = int(current_q)
        question = get_object_or_404(Question, id=current_q, exam=exam)
    else:
        question = questions[0]
    answer = answers.get(question.id)
    options = question.options.all() if question.type == QuestionType.MULTIPLE_CHOICE else None

    # Hitung index, prev, next
    q_ids = [q.id for q in questions]
    idx = q_ids.index(question.id)
    prev_id = q_ids[idx - 1] if idx > 0 else None
    next_id = q_ids[idx + 1] if idx < len(q_ids) - 1 else None

    return render(request, 'exam/exam_session.html', {
        'session': session,
        'exam': exam,
        'question': question,
        'questions': questions,
        'options': options,
        'answer': answer,
        'prev_id': prev_id,
        'next_id': next_id,
    })

@login_required
def submit_answer(request, course_id, session_id):
    session = get_object_or_404(ExamSession, id=session_id, student=request.user)
    exam = session.exam
    if request.method == 'POST':
        question_id = int(request.POST['question_id'])
        question = get_object_or_404(Question, id=question_id, exam=exam)
        answer, _ = Answer.objects.get_or_create(exam_session=session, question=question)
        if question.type == QuestionType.MULTIPLE_CHOICE:
            selected_option_id = request.POST.get('selected_option')
            if selected_option_id:
                option = get_object_or_404(QuestionOption, id=selected_option_id, question=question)
                answer.selected_option = option
                answer.text_answer = ''
                # Otomatis beri nilai untuk pilihan ganda
                if option.is_correct:
                    answer.points_earned = question.points
                else:
                    answer.points_earned = 0
        elif question.type == QuestionType.ESSAY:
            answer.text_answer = request.POST.get('text_answer', '')
            answer.selected_option = None
        answer.save()
        
        # Jika tombol Simpan Jawaban (finish) ditekan, hitung nilai dan selesaikan ujian
        if request.POST.get('finish'):
            # Tandai ujian sebagai selesai
            session.status = ExamSessionStatus.SUBMITTED
            session.end_time = timezone.now()
            
            # Hitung nilai untuk soal pilihan ganda
            total_points = exam.total_points
            earned_points = 0
            
            for ans in Answer.objects.filter(exam_session=session):
                if ans.question.type == QuestionType.MULTIPLE_CHOICE:
                    if ans.selected_option and ans.selected_option.is_correct:
                        earned_points += ans.question.points
            
            # Hitung persentase nilai
            if total_points > 0:
                score_percentage = (earned_points / total_points) * 100
            else:
                score_percentage = 0
                
            session.score = score_percentage
            session.passed = score_percentage >= exam.passing_score
            session.save()
            
            # Redirect ke halaman hasil ujian
            return redirect('exam_result', course_id=course_id, session_id=session_id)
            
        # Jika Next ditekan, lanjut ke soal berikutnya
        next_q = request.POST.get('next_q')
        if next_q:
            url = reverse('exam_session', args=[course_id, session_id]) + f'?q={next_q}'
            return redirect(url)
        # Default: tetap di soal ini
        url = reverse('exam_session', args=[course_id, session_id]) + f'?q={question_id}'
        return redirect(url)
    return redirect('exam_session', course_id=course_id, session_id=session_id)

@login_required
def exam_result(request, course_id, session_id):
    """View untuk menampilkan hasil ujian"""
    session = get_object_or_404(ExamSession, id=session_id)
    exam = session.exam
    course = get_object_or_404(Course, id=course_id)
    
    # Hanya pemilik session atau instruktur yang boleh melihat hasil
    if request.user != session.student and request.user != course.instructor:
        if not request.user.is_staff and not request.user.is_superuser:
            messages.error(request, "Anda tidak memiliki akses untuk melihat hasil ujian ini.")
            return redirect('course_detail', course_id=course_id)
    
    # Ambil semua jawaban untuk session ini
    answers = Answer.objects.filter(exam_session=session).select_related('question', 'selected_option')
    
    return render(request, 'exam/exam_result.html', {
        'session': session,
        'exam': exam,
        'course': course,
        'answers': answers,
    })

class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = ['title', 'description', 'duration_minutes', 'passing_score']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3'}),
            'description': forms.Textarea(attrs={'class': 'mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3', 'rows': 3}),
            'duration_minutes': forms.NumberInput(attrs={'class': 'mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3', 'min': 1}),
            'passing_score': forms.NumberInput(attrs={'class': 'mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3', 'min': 0, 'max': 100}),
        }

@login_required
def add_exam(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if request.user != course.instructor and not request.user.is_staff and not request.user.is_superuser:
        return HttpResponseForbidden("Anda tidak berhak menambah ujian pada kursus ini.")
    if request.method == 'POST':
        form = ExamForm(request.POST)
        if form.is_valid():
            exam = form.save(commit=False)
            exam.course = course
            exam.save()
            # Redirect ke halaman tambah soal (add_question)
            return redirect('add_question', course_id=course.id, exam_id=exam.id)
    else:
        form = ExamForm()
    return render(request, 'exam/exam_form.html', {'form': form, 'course': course, 'action': 'Tambah'})

class QuestionForm(ModelForm):
    class Meta:
        model = Question
        fields = ['text', 'points', 'order']
        widgets = {
            'text': forms.Textarea(attrs={'class': 'mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3', 'rows': 3}),
            'points': forms.NumberInput(attrs={'class': 'mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3', 'min': 1}),
            'order': forms.NumberInput(attrs={'class': 'mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3', 'min': 1}),
        }

QuestionOptionFormSet = inlineformset_factory(
    Question, QuestionOption,
    fields=['text', 'is_correct', 'order'],
    extra=4, min_num=4, max_num=4, validate_min=True, validate_max=True
)

@login_required
def add_question(request, course_id, exam_id):
    course = get_object_or_404(Course, id=course_id)
    exam = get_object_or_404(Exam, id=exam_id, course=course)
    if request.user != course.instructor and not request.user.is_staff and not request.user.is_superuser:
        return HttpResponseForbidden("Anda tidak berhak menambah soal pada ujian ini.")
    if request.method == 'POST':
        q_form = QuestionForm(request.POST)
        formset = QuestionOptionFormSet(request.POST)
        if q_form.is_valid() and formset.is_valid():
            question = q_form.save(commit=False)
            question.exam = exam
            question.type = QuestionType.MULTIPLE_CHOICE
            question.save()
            formset.instance = question
            formset.save()
            # Redirect ke halaman detail exam atau tambah soal lagi
            if 'add_another' in request.POST:
                return redirect('add_question', course_id=course.id, exam_id=exam.id)
            return redirect('exam_detail', course_id=course.id, exam_id=exam.id)
    else:
        q_form = QuestionForm()
        formset = QuestionOptionFormSet()
    return render(request, 'exam/add_question.html', {
        'course': course,
        'exam': exam,
        'q_form': q_form,
        'formset': formset,
    })

@login_required
def delete_exam(request, course_id, exam_id):
    course = get_object_or_404(Course, id=course_id)
    exam = get_object_or_404(Exam, id=exam_id, course=course)
    if request.user != course.instructor and not request.user.is_staff and not request.user.is_superuser:
        return HttpResponseForbidden("Anda tidak berhak menghapus ujian ini.")
    if request.method == 'POST':
        exam.delete()
        return redirect('exam_list', course_id=course.id)
    return render(request, 'exam/exam_confirm_delete.html', {'course': course, 'exam': exam})
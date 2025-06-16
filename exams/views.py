from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from exams.models import Exam, ExamSession, Question, QuestionOption, Answer, ExamSessionStatus, QuestionType
from courses.models import Course, Enrollment
from django.urls import reverse

@login_required
def exam_list(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    # Hanya yang sudah enroll
    if not Enrollment.objects.filter(student=request.user, course=course).exists():
        return render(request, 'exam/not_enrolled.html', {'course': course})
    exams = Exam.objects.filter(course=course)
    return render(request, 'exam/exam_list.html', {'course': course, 'exams': exams})

@login_required
def exam_detail(request, course_id, exam_id):
    course = get_object_or_404(Course, id=course_id)
    exam = get_object_or_404(Exam, id=exam_id, course=course)
    if not Enrollment.objects.filter(student=request.user, course=course).exists():
        return render(request, 'exam/not_enrolled.html', {'course': course})
    # Cek session aktif
    session = ExamSession.objects.filter(exam=exam, student=request.user, status__in=[ExamSessionStatus.STARTED, ExamSessionStatus.IN_PROGRESS]).first()
    return render(request, 'exam/exam_detail.html', {
        'course': course,
        'exam': exam,
        'session': session,
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
        elif question.type == QuestionType.ESSAY:
            answer.text_answer = request.POST.get('text_answer', '')
            answer.selected_option = None
        answer.save()
        # Jika tombol Simpan Jawaban (finish) ditekan, redirect ke exam list
        if request.POST.get('finish'):
            return redirect('exam_list', course_id=course_id)
        # Jika Next ditekan, lanjut ke soal berikutnya
        next_q = request.POST.get('next_q')
        if next_q:
            url = reverse('exam_session', args=[course_id, session_id]) + f'?q={next_q}'
            return redirect(url)
        # Default: tetap di soal ini
        url = reverse('exam_session', args=[course_id, session_id]) + f'?q={question_id}'
        return redirect(url)
    return redirect('exam_session', course_id=course_id, session_id=session_id)
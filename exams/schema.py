import graphene
from graphene_django import DjangoObjectType
from graphql_jwt.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import models
from django.utils import timezone

from .models import (
    Exam, Question, QuestionOption, ExamSession, 
    Answer, ExamSessionStatus, QuestionType
)
from courses.models import Course, CourseStatus

class QuestionTypeEnum(graphene.Enum):
    MULTIPLE_CHOICE = QuestionType.MULTIPLE_CHOICE
    ESSAY = QuestionType.ESSAY

class ExamSessionStatusEnum(graphene.Enum):
    STARTED = ExamSessionStatus.STARTED
    IN_PROGRESS = ExamSessionStatus.IN_PROGRESS
    SUBMITTED = ExamSessionStatus.SUBMITTED
    GRADED = ExamSessionStatus.GRADED

class ExamType(DjangoObjectType):
    class Meta:
        model = Exam
        fields = '__all__'
    
    total_points = graphene.Int()
    question_count = graphene.Int()
    
    def resolve_total_points(self, info):
        return self.total_points
    
    def resolve_question_count(self, info):
        return self.question_count

class QuestionType(DjangoObjectType):
    class Meta:
        model = Question
        fields = '__all__'

class QuestionOptionType(DjangoObjectType):
    class Meta:
        model = QuestionOption
        # Don't expose correct answer to students
        exclude = ('is_correct',)

class QuestionOptionAdminType(DjangoObjectType):
    class Meta:
        model = QuestionOption
        fields = '__all__'

class ExamSessionType(DjangoObjectType):
    class Meta:
        model = ExamSession
        fields = '__all__'
    
    time_elapsed = graphene.Float()
    
    def resolve_time_elapsed(self, info):
        return self.time_elapsed

class AnswerType(DjangoObjectType):
    class Meta:
        model = Answer
        fields = '__all__'

class Query(graphene.ObjectType):
    exams = graphene.List(
        ExamType,
        course_id=graphene.ID(required=True)
    )
    exam = graphene.Field(ExamType, id=graphene.ID(required=True))
    
    questions = graphene.List(
        QuestionType,
        exam_id=graphene.ID(required=True)
    )
    
    question = graphene.Field(QuestionType, id=graphene.ID(required=True))
    
    question_options = graphene.List(
        QuestionOptionType,
        question_id=graphene.ID(required=True)
    )
    
    exam_sessions = graphene.List(
        ExamSessionType,
        exam_id=graphene.ID(),
        student_id=graphene.ID()
    )
    
    exam_session = graphene.Field(ExamSessionType, id=graphene.ID(required=True))
    
    my_exams = graphene.List(ExamType)
    
    @login_required
    def resolve_exams(self, info, course_id):
        user = info.context.user
        
        try:
            course = Course.objects.get(pk=course_id)
        except Course.DoesNotExist:
            return Exam.objects.none()
        
        # Check permissions
        if course.status != CourseStatus.PUBLISHED:
            if user.is_student and not course.students.filter(id=user.id).exists():
                return Exam.objects.none()
            if user.is_instructor and course.instructor.id != user.id and not (user.is_staff or user.is_superuser):
                return Exam.objects.none()
        
        return Exam.objects.filter(course_id=course_id)
    
    @login_required
    def resolve_exam(self, info, id):
        user = info.context.user
        
        try:
            exam = Exam.objects.get(pk=id)
        except Exam.DoesNotExist:
            return None
        
        course = exam.course
        
        # Check permissions
        if course.status != CourseStatus.PUBLISHED:
            if user.is_student and not course.students.filter(id=user.id).exists():
                return None
            if user.is_instructor and course.instructor.id != user.id and not (user.is_staff or user.is_superuser):
                return None
        
        # Check if exam is accessible (time constraints)
        if user.is_student:
            now = timezone.now()
            if exam.available_from and exam.available_from > now:
                return None
            if exam.available_until and exam.available_until < now:
                return None
        
        return exam
    
    @login_required
    def resolve_questions(self, info, exam_id):
        user = info.context.user
        
        try:
            exam = Exam.objects.get(pk=exam_id)
        except Exam.DoesNotExist:
            return Question.objects.none()
        
        course = exam.course
        
        # Check permissions (similar to exam resolver)
        if course.status != CourseStatus.PUBLISHED:
            if user.is_student and not course.students.filter(id=user.id).exists():
                return Question.objects.none()
            if user.is_instructor and course.instructor.id != user.id and not (user.is_staff or user.is_superuser):
                return Question.objects.none()
        
        # For students with an active session, return questions
        if user.is_student:
            # Check if there's an active session
            active_session = ExamSession.objects.filter(
                exam_id=exam_id,
                student=user,
                status__in=[ExamSessionStatus.STARTED, ExamSessionStatus.IN_PROGRESS]
            ).first()
            
            if active_session:
                return Question.objects.filter(exam_id=exam_id)
            return Question.objects.none()
        
        # For instructors and staff, return all questions
        return Question.objects.filter(exam_id=exam_id)
    
    @login_required
    def resolve_question(self, info, id):
        user = info.context.user
        
        try:
            question = Question.objects.get(pk=id)
        except Question.DoesNotExist:
            return None
        
        exam = question.exam
        course = exam.course
        
        # Check permissions (similar to questions resolver)
        if course.status != CourseStatus.PUBLISHED:
            if user.is_student and not course.students.filter(id=user.id).exists():
                return None
            if user.is_instructor and course.instructor.id != user.id and not (user.is_staff or user.is_superuser):
                return None
        
        # For students, check if there's an active session
        if user.is_student:
            active_session = ExamSession.objects.filter(
                exam=exam,
                student=user,
                status__in=[ExamSessionStatus.STARTED, ExamSessionStatus.IN_PROGRESS]
            ).exists()
            
            if not active_session:
                return None
        
        return question
    
    @login_required
    def resolve_question_options(self, info, question_id):
        user = info.context.user
        
        try:
            question = Question.objects.get(pk=question_id)
        except Question.DoesNotExist:
            return QuestionOption.objects.none()
        
        exam = question.exam
        course = exam.course
        
        # Check permissions (similar to question resolver)
        if course.status != CourseStatus.PUBLISHED:
            if user.is_student and not course.students.filter(id=user.id).exists():
                return QuestionOption.objects.none()
            if user.is_instructor and course.instructor.id != user.id and not (user.is_staff or user.is_superuser):
                return QuestionOption.objects.none()
        
        # For students, check if there's an active session
        if user.is_student:
            active_session = ExamSession.objects.filter(
                exam=exam,
                student=user,
                status__in=[ExamSessionStatus.STARTED, ExamSessionStatus.IN_PROGRESS]
            ).exists()
            
            if not active_session:
                return QuestionOption.objects.none()
        
        return QuestionOption.objects.filter(question_id=question_id)
    
    @login_required
    def resolve_exam_sessions(self, info, exam_id=None, student_id=None):
        user = info.context.user
        
        # Students can only see their own sessions
        if user.is_student:
            qs = ExamSession.objects.filter(student=user)
            if exam_id:
                qs = qs.filter(exam_id=exam_id)
            return qs
        
        # Instructors can see sessions for their courses
        if user.is_instructor and not (user.is_staff or user.is_superuser):
            qs = ExamSession.objects.filter(exam__course__instructor=user)
            if exam_id:
                qs = qs.filter(exam_id=exam_id)
            if student_id:
                qs = qs.filter(student_id=student_id)
            return qs
        
        # Admins can see all sessions
        qs = ExamSession.objects.all()
        if exam_id:
            qs = qs.filter(exam_id=exam_id)
        if student_id:
            qs = qs.filter(student_id=student_id)
        return qs
    
    @login_required
    def resolve_exam_session(self, info, id):
        user = info.context.user
        
        try:
            session = ExamSession.objects.get(pk=id)
        except ExamSession.DoesNotExist:
            return None
        
        # Students can only see their own sessions
        if user.is_student and session.student.id != user.id:
            return None
        
        # Instructors can only see sessions for their courses
        if user.is_instructor and not (user.is_staff or user.is_superuser):
            if session.exam.course.instructor.id != user.id:
                return None
        
        return session
    
    @login_required
    def resolve_my_exams(self, info):
        user = info.context.user
        
        if user.is_student:
            # Get exams for courses the student is enrolled in
            courses = user.courses_enrolled.all()
            return Exam.objects.filter(course__in=courses, course__status=CourseStatus.PUBLISHED)
        
        if user.is_instructor and not (user.is_staff or user.is_superuser):
            # Get exams for courses the instructor is teaching
            return Exam.objects.filter(course__instructor=user)
        
        # Admins can see all exams
        return Exam.objects.all()

class StartExam(graphene.Mutation):
    exam_session = graphene.Field(ExamSessionType)
    success = graphene.Boolean()
    message = graphene.String()
    
    class Arguments:
        exam_id = graphene.ID(required=True)
    
    @login_required
    def mutate(self, info, exam_id):
        user = info.context.user
        
        # Only students can start exams
        if not user.is_student:
            return StartExam(
                success=False,
                message="Only students can take exams",
                exam_session=None
            )
        
        try:
            exam = Exam.objects.get(pk=exam_id)
        except Exam.DoesNotExist:
            return StartExam(
                success=False,
                message="Exam not found",
                exam_session=None
            )
        
        # Check if the student is enrolled in the course
        if not exam.course.students.filter(id=user.id).exists():
            return StartExam(
                success=False,
                message="You must be enrolled in this course to take this exam",
                exam_session=None
            )
        
        # Check if the exam is available (time constraints)
        now = timezone.now()
        if exam.available_from and exam.available_from > now:
            return StartExam(
                success=False,
                message="This exam is not available yet",
                exam_session=None
            )
        
        if exam.available_until and exam.available_until < now:
            return StartExam(
                success=False,
                message="This exam is no longer available",
                exam_session=None
            )
        
        # Check if the student already has an active session
        existing_session = ExamSession.objects.filter(
            exam=exam,
            student=user,
            status__in=[ExamSessionStatus.STARTED, ExamSessionStatus.IN_PROGRESS]
        ).first()
        
        if existing_session:
            return StartExam(
                success=True,
                message="You have already started this exam",
                exam_session=existing_session
            )
        
        # Check if the student has already completed this exam
        completed_session = ExamSession.objects.filter(
            exam=exam,
            student=user,
            status__in=[ExamSessionStatus.SUBMITTED, ExamSessionStatus.GRADED]
        ).first()
        
        if completed_session:
            return StartExam(
                success=False,
                message="You have already completed this exam",
                exam_session=completed_session
            )
        
        # Create a new exam session
        session = ExamSession(
            exam=exam,
            student=user,
            status=ExamSessionStatus.STARTED
        )
        session.save()
        
        return StartExam(
            success=True,
            message="Exam started successfully",
            exam_session=session
        )

class SubmitAnswer(graphene.Mutation):
    answer = graphene.Field(AnswerType)
    success = graphene.Boolean()
    message = graphene.String()
    
    class Arguments:
        exam_session_id = graphene.ID(required=True)
        question_id = graphene.ID(required=True)
        selected_option_id = graphene.ID()
        text_answer = graphene.String()
    
    @login_required
    def mutate(self, info, exam_session_id, question_id, selected_option_id=None, text_answer=None):
        user = info.context.user
        
        try:
            session = ExamSession.objects.get(pk=exam_session_id)
        except ExamSession.DoesNotExist:
            return SubmitAnswer(
                success=False,
                message="Exam session not found",
                answer=None
            )
        
        # Check if this is the student's session
        if session.student.id != user.id:
            return SubmitAnswer(
                success=False,
                message="This is not your exam session",
                answer=None
            )
        
        # Check if the session is active
        if session.status not in [ExamSessionStatus.STARTED, ExamSessionStatus.IN_PROGRESS]:
            return SubmitAnswer(
                success=False,
                message="This exam session is no longer active",
                answer=None
            )
        
        try:
            question = Question.objects.get(pk=question_id)
        except Question.DoesNotExist:
            return SubmitAnswer(
                success=False,
                message="Question not found",
                answer=None
            )
        
        # Check if the question belongs to the exam
        if question.exam.id != session.exam.id:
            return SubmitAnswer(
                success=False,
                message="Question does not belong to this exam",
                answer=None
            )
        
        # Update session status to IN_PROGRESS if it's just STARTED
        if session.status == ExamSessionStatus.STARTED:
            session.status = ExamSessionStatus.IN_PROGRESS
            session.save()
        
        # Look for an existing answer to this question
        answer = Answer.objects.filter(
            exam_session=session,
            question=question
        ).first()
        
        if not answer:
            # Create a new answer
            answer = Answer(
                exam_session=session,
                question=question
            )
        
        # Update the answer based on question type
        if question.type == QuestionType.MULTIPLE_CHOICE:
            if selected_option_id:
                try:
                    option = QuestionOption.objects.get(pk=selected_option_id)
                    # Verify the option belongs to the question
                    if option.question.id != question.id:
                        return SubmitAnswer(
                            success=False,
                            message="Option does not belong to this question",
                            answer=None
                        )
                    answer.selected_option = option
                except QuestionOption.DoesNotExist:
                    return SubmitAnswer(
                        success=False,
                        message="Option not found",
                        answer=None
                    )
            else:
                return SubmitAnswer(
                    success=False,
                    message="You must select an option for multiple choice questions",
                    answer=None
                )
        elif question.type == QuestionType.ESSAY:
            if text_answer:
                answer.text_answer = text_answer
            else:
                return SubmitAnswer(
                    success=False,
                    message="You must provide a text answer for essay questions",
                    answer=None
                )
        
        answer.save()
        
        return SubmitAnswer(
            success=True,
            message="Answer submitted successfully",
            answer=answer
        )

class FinishExam(graphene.Mutation):
    exam_session = graphene.Field(ExamSessionType)
    success = graphene.Boolean()
    message = graphene.String()
    
    class Arguments:
        exam_session_id = graphene.ID(required=True)
    
    @login_required
    def mutate(self, info, exam_session_id):
        user = info.context.user
        
        try:
            session = ExamSession.objects.get(pk=exam_session_id)
        except ExamSession.DoesNotExist:
            return FinishExam(
                success=False,
                message="Exam session not found",
                exam_session=None
            )
        
        # Check if this is the student's session
        if session.student.id != user.id:
            return FinishExam(
                success=False,
                message="This is not your exam session",
                exam_session=None
            )
        
        # Check if the session is active
        if session.status not in [ExamSessionStatus.STARTED, ExamSessionStatus.IN_PROGRESS]:
            return FinishExam(
                success=False,
                message="This exam session is no longer active",
                exam_session=None
            )
        
        # Auto-grade multiple choice questions
        exam = session.exam
        total_points = 0
        earned_points = 0
        
        for question in exam.questions.all():
            total_points += question.points
            
            # Get student's answer for this question
            answer = Answer.objects.filter(
                exam_session=session,
                question=question
            ).first()
            
            if not answer:
                continue
            
            # Auto-grade multiple choice questions
            if question.type == QuestionType.MULTIPLE_CHOICE and answer.selected_option:
                if answer.selected_option.is_correct:
                    answer.points_earned = question.points
                else:
                    answer.points_earned = 0
                answer.save()
                earned_points += answer.points_earned
        
        # Calculate score as a percentage
        score = (earned_points / total_points * 100) if total_points > 0 else 0
        
        # Update session
        session.status = ExamSessionStatus.SUBMITTED
        session.end_time = timezone.now()
        session.score = score
        session.passed = score >= exam.passing_score
        session.save()
        
        return FinishExam(
            success=True,
            message="Exam finished successfully",
            exam_session=session
        )

class GradeEssayAnswer(graphene.Mutation):
    answer = graphene.Field(AnswerType)
    success = graphene.Boolean()
    
    class Arguments:
        answer_id = graphene.ID(required=True)
        points_earned = graphene.Float(required=True)
        feedback = graphene.String()
    
    @login_required
    def mutate(self, info, answer_id, points_earned, feedback=None):
        user = info.context.user
        
        try:
            answer = Answer.objects.get(pk=answer_id)
        except Answer.DoesNotExist:
            return GradeEssayAnswer(success=False, answer=None)
        
        question = answer.question
        exam = question.exam
        course = exam.course
        
        # Only the instructor or staff can grade answers
        if course.instructor.id != user.id and not (user.is_staff or user.is_superuser):
            raise PermissionDenied("You don't have permission to grade this answer")
        
        # Check if this is an essay question
        if question.type != QuestionType.ESSAY:
            return GradeEssayAnswer(
                success=False,
                answer=None
            )
        
        # Update the answer
        answer.points_earned = min(points_earned, question.points)  # Ensure points don't exceed max
        answer.feedback = feedback or ""
        answer.save()
        
        # Update the exam session's score if all questions are graded
        session = answer.exam_session
        if session.status == ExamSessionStatus.SUBMITTED:
            # Check if all essay questions have been graded
            essay_questions = session.exam.questions.filter(type=QuestionType.ESSAY)
            graded_answers = Answer.objects.filter(
                exam_session=session,
                question__in=essay_questions,
                points_earned__isnull=False
            ).count()
            
            if graded_answers == essay_questions.count():
                # All essay questions graded, update total score
                total_points = 0
                earned_points = 0
                
                for q in session.exam.questions.all():
                    total_points += q.points
                    a = Answer.objects.filter(exam_session=session, question=q).first()
                    if a and a.points_earned is not None:
                        earned_points += a.points_earned
                
                # Calculate score as a percentage
                score = (earned_points / total_points * 100) if total_points > 0 else 0
                
                # Update session
                session.status = ExamSessionStatus.GRADED
                session.score = score
                session.passed = score >= exam.passing_score
                session.save()
        
        return GradeEssayAnswer(success=True, answer=answer)

class Mutation(graphene.ObjectType):
    start_exam = StartExam.Field()
    submit_answer = SubmitAnswer.Field()
    finish_exam = FinishExam.Field()
    grade_essay_answer = GradeEssayAnswer.Field() 
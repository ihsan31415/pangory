import graphene
from graphene_django import DjangoObjectType
from graphql_jwt.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.utils import timezone

from .models import Certificate
from courses.models import Course, CourseStatus
from exams.models import ExamSession, ExamSessionStatus

class CertificateType(DjangoObjectType):
    class Meta:
        model = Certificate
        fields = '__all__'
    
    is_valid = graphene.Boolean()
    certificate_url = graphene.String()
    
    def resolve_is_valid(self, info):
        return self.is_valid
    
    def resolve_certificate_url(self, info):
        return self.certificate_url

class Query(graphene.ObjectType):
    certificates = graphene.List(
        CertificateType,
        course_id=graphene.ID(),
        user_id=graphene.ID()
    )
    certificate = graphene.Field(CertificateType, id=graphene.ID(required=True))
    my_certificates = graphene.List(CertificateType)
    
    @login_required
    def resolve_certificates(self, info, course_id=None, user_id=None):
        user = info.context.user
        
        # Students can only see their own certificates
        if user.is_student:
            qs = Certificate.objects.filter(user=user)
            if course_id:
                qs = qs.filter(course_id=course_id)
            return qs
        
        # Instructors can see certificates for their courses
        if user.is_instructor and not (user.is_staff or user.is_superuser):
            qs = Certificate.objects.filter(course__instructor=user)
            if course_id:
                qs = qs.filter(course_id=course_id)
            if user_id:
                qs = qs.filter(user_id=user_id)
            return qs
        
        # Admins can see all certificates
        qs = Certificate.objects.all()
        if course_id:
            qs = qs.filter(course_id=course_id)
        if user_id:
            qs = qs.filter(user_id=user_id)
        return qs
    
    @login_required
    def resolve_certificate(self, info, id):
        user = info.context.user
        
        try:
            certificate = Certificate.objects.get(pk=id)
        except Certificate.DoesNotExist:
            return None
        
        # Students can only see their own certificates
        if user.is_student and certificate.user.id != user.id:
            return None
        
        # Instructors can only see certificates for their courses
        if user.is_instructor and not (user.is_staff or user.is_superuser):
            if certificate.course.instructor.id != user.id:
                return None
        
        return certificate
    
    @login_required
    def resolve_my_certificates(self, info):
        user = info.context.user
        return Certificate.objects.filter(user=user)

class GenerateCertificate(graphene.Mutation):
    certificate = graphene.Field(CertificateType)
    success = graphene.Boolean()
    message = graphene.String()
    
    class Arguments:
        exam_session_id = graphene.ID(required=True)
    
    @login_required
    def mutate(self, info, exam_session_id):
        user = info.context.user
        
        # Only instructors and admins can generate certificates
        if user.is_student:
            return GenerateCertificate(
                success=False,
                message="Only instructors and administrators can generate certificates",
                certificate=None
            )
        
        try:
            exam_session = ExamSession.objects.get(pk=exam_session_id)
        except ExamSession.DoesNotExist:
            return GenerateCertificate(
                success=False,
                message="Exam session not found",
                certificate=None
            )
        
        # Check if the instructor is teaching this course
        course = exam_session.exam.course
        if user.is_instructor and course.instructor.id != user.id and not (user.is_staff or user.is_superuser):
            return GenerateCertificate(
                success=False,
                message="You don't have permission to generate certificates for this course",
                certificate=None
            )
        
        # Check if the exam session is completed and passed
        if exam_session.status != ExamSessionStatus.GRADED:
            return GenerateCertificate(
                success=False,
                message="The exam has not been graded yet",
                certificate=None
            )
        
        if not exam_session.passed:
            return GenerateCertificate(
                success=False,
                message="The student did not pass the exam",
                certificate=None
            )
        
        # Check if a certificate already exists
        existing_certificate = Certificate.objects.filter(
            user=exam_session.student,
            course=course
        ).first()
        
        if existing_certificate:
            return GenerateCertificate(
                success=False,
                message="A certificate already exists for this student and course",
                certificate=existing_certificate
            )
        
        # Create a new certificate
        certificate = Certificate(
            user=exam_session.student,
            course=course,
            exam_session=exam_session,
            issue_date=timezone.now()
        )
        certificate.save()
        
        return GenerateCertificate(
            success=True,
            message="Certificate generated successfully",
            certificate=certificate
        )

class Mutation(graphene.ObjectType):
    generate_certificate = GenerateCertificate.Field() 
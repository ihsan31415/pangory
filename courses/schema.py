import graphene
from graphene_django import DjangoObjectType
from graphql_jwt.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import models

from .models import Course, Module, Material, MaterialType, Task, TaskSubmission, Enrollment, CourseStatus
from accounts.models import User, UserRole

class CourseStatusEnum(graphene.Enum):
    DRAFT = CourseStatus.DRAFT
    PUBLISHED = CourseStatus.PUBLISHED
    ARCHIVED = CourseStatus.ARCHIVED

class MaterialTypeEnum(graphene.Enum):
    VIDEO = MaterialType.VIDEO
    PDF = MaterialType.PDF
    TEXT = MaterialType.TEXT
    QUIZ_LINK = MaterialType.QUIZ_LINK

class CourseType(DjangoObjectType):
    class Meta:
        model = Course
        fields = '__all__'
    
    student_count = graphene.Int()
    module_count = graphene.Int()
    is_enrolled = graphene.Boolean()
    
    def resolve_student_count(self, info):
        return self.student_count
    
    def resolve_module_count(self, info):
        return self.module_count
    
    def resolve_is_enrolled(self, info):
        user = info.context.user
        if user.is_authenticated:
            return self.students.filter(id=user.id).exists()
        return False

class ModuleType(DjangoObjectType):
    class Meta:
        model = Module
        fields = '__all__'

class MaterialType(DjangoObjectType):
    class Meta:
        model = Material
        fields = '__all__'

class TaskType(DjangoObjectType):
    class Meta:
        model = Task
        fields = '__all__'
    
    has_submitted = graphene.Boolean()
    
    def resolve_has_submitted(self, info):
        user = info.context.user
        if user.is_authenticated:
            return self.submissions.filter(student=user).exists()
        return False

class TaskSubmissionType(DjangoObjectType):
    class Meta:
        model = TaskSubmission
        fields = '__all__'

class EnrollmentType(DjangoObjectType):
    class Meta:
        model = Enrollment
        fields = '__all__'

class Query(graphene.ObjectType):
    courses = graphene.List(
        CourseType,
        status=CourseStatusEnum(),
        instructor_id=graphene.ID(),
        search=graphene.String(),
        skip=graphene.Int(),
        limit=graphene.Int()
    )
    course = graphene.Field(CourseType, id=graphene.ID(required=True))
    
    modules = graphene.List(ModuleType, course_id=graphene.ID(required=True))
    module = graphene.Field(ModuleType, id=graphene.ID(required=True))
    
    materials = graphene.List(MaterialType, module_id=graphene.ID(required=True))
    material = graphene.Field(MaterialType, id=graphene.ID(required=True))
    
    tasks = graphene.List(TaskType, course_id=graphene.ID(required=True))
    task = graphene.Field(TaskType, id=graphene.ID(required=True))
    
    my_enrollments = graphene.List(EnrollmentType)
    my_task_submissions = graphene.List(TaskSubmissionType, course_id=graphene.ID())
    
    def resolve_courses(self, info, status=None, instructor_id=None, search=None, skip=None, limit=None):
        user = info.context.user
        
        # Filter published courses for unauthenticated or student users
        if not user.is_authenticated or user.is_student:
            qs = Course.objects.filter(status=CourseStatus.PUBLISHED)
        else:
            qs = Course.objects.all()
            
            # Instructors can only see their own courses
            if user.is_instructor and not (user.is_staff or user.is_superuser):
                qs = qs.filter(instructor=user)
        
        if status:
            qs = qs.filter(status=status)
        
        if instructor_id:
            qs = qs.filter(instructor_id=instructor_id)
        
        if search:
            qs = qs.filter(
                models.Q(title__icontains=search) |
                models.Q(description__icontains=search)
            )
        
        if skip:
            qs = qs[skip:]
        
        if limit:
            qs = qs[:limit]
        
        return qs
    
    def resolve_course(self, info, id):
        user = info.context.user
        course = Course.objects.get(pk=id)
        
        # Check permissions
        if course.status != CourseStatus.PUBLISHED:
            if not user.is_authenticated:
                return None
            if user.is_student and not course.students.filter(id=user.id).exists():
                return None
            if user.is_instructor and course.instructor.id != user.id and not (user.is_staff or user.is_superuser):
                return None
        
        return course
    
    @login_required
    def resolve_modules(self, info, course_id):
        user = info.context.user
        course = Course.objects.get(pk=course_id)
        
        # Check permissions (similar to course resolver)
        if course.status != CourseStatus.PUBLISHED:
            if user.is_student and not course.students.filter(id=user.id).exists():
                return Module.objects.none()
            if user.is_instructor and course.instructor.id != user.id and not (user.is_staff or user.is_superuser):
                return Module.objects.none()
        
        return Module.objects.filter(course_id=course_id)
    
    @login_required
    def resolve_module(self, info, id):
        user = info.context.user
        module = Module.objects.get(pk=id)
        course = module.course
        
        # Check permissions (similar to course resolver)
        if course.status != CourseStatus.PUBLISHED:
            if user.is_student and not course.students.filter(id=user.id).exists():
                return None
            if user.is_instructor and course.instructor.id != user.id and not (user.is_staff or user.is_superuser):
                return None
        
        return module
    
    @login_required
    def resolve_materials(self, info, module_id):
        user = info.context.user
        module = Module.objects.get(pk=module_id)
        course = module.course
        
        # Check permissions (similar to module resolver)
        if course.status != CourseStatus.PUBLISHED:
            if user.is_student and not course.students.filter(id=user.id).exists():
                return Material.objects.none()
            if user.is_instructor and course.instructor.id != user.id and not (user.is_staff or user.is_superuser):
                return Material.objects.none()
        
        return Material.objects.filter(module_id=module_id)
    
    @login_required
    def resolve_material(self, info, id):
        user = info.context.user
        material = Material.objects.get(pk=id)
        course = material.module.course
        
        # Check permissions (similar to module resolver)
        if course.status != CourseStatus.PUBLISHED:
            if user.is_student and not course.students.filter(id=user.id).exists():
                return None
            if user.is_instructor and course.instructor.id != user.id and not (user.is_staff or user.is_superuser):
                return None
        
        return material
    
    @login_required
    def resolve_tasks(self, info, course_id):
        user = info.context.user
        course = Course.objects.get(pk=course_id)
        
        # Check permissions (similar to course resolver)
        if course.status != CourseStatus.PUBLISHED:
            if user.is_student and not course.students.filter(id=user.id).exists():
                return Task.objects.none()
            if user.is_instructor and course.instructor.id != user.id and not (user.is_staff or user.is_superuser):
                return Task.objects.none()
        
        return Task.objects.filter(course_id=course_id)
    
    @login_required
    def resolve_task(self, info, id):
        user = info.context.user
        task = Task.objects.get(pk=id)
        course = task.course
        
        # Check permissions (similar to course resolver)
        if course.status != CourseStatus.PUBLISHED:
            if user.is_student and not course.students.filter(id=user.id).exists():
                return None
            if user.is_instructor and course.instructor.id != user.id and not (user.is_staff or user.is_superuser):
                return None
        
        return task
    
    @login_required
    def resolve_my_enrollments(self, info):
        user = info.context.user
        return Enrollment.objects.filter(student=user)
    
    @login_required
    def resolve_my_task_submissions(self, info, course_id=None):
        user = info.context.user
        
        if course_id:
            return TaskSubmission.objects.filter(student=user, task__course_id=course_id)
        
        return TaskSubmission.objects.filter(student=user)

class CreateCourse(graphene.Mutation):
    course = graphene.Field(CourseType)
    success = graphene.Boolean()
    
    class Arguments:
        title = graphene.String(required=True)
        description = graphene.String(required=True)
        price = graphene.Decimal()
    
    @login_required
    def mutate(self, info, title, description, price=None):
        user = info.context.user
        
        # Only instructors and staff can create courses
        if not (user.is_instructor or user.is_staff or user.is_superuser):
            raise PermissionDenied("You don't have permission to create courses")
        
        course = Course(
            title=title,
            description=description,
            instructor=user,
            price=price if price is not None else 0.00,
            status=CourseStatus.DRAFT
        )
        course.save()
        
        return CreateCourse(success=True, course=course)

class UpdateCourse(graphene.Mutation):
    course = graphene.Field(CourseType)
    success = graphene.Boolean()
    
    class Arguments:
        id = graphene.ID(required=True)
        title = graphene.String()
        description = graphene.String()
        price = graphene.Decimal()
        status = CourseStatusEnum()
    
    @login_required
    def mutate(self, info, id, title=None, description=None, price=None, status=None):
        user = info.context.user
        
        try:
            course = Course.objects.get(pk=id)
        except Course.DoesNotExist:
            return UpdateCourse(success=False, course=None)
        
        # Only the instructor or staff can update the course
        if course.instructor.id != user.id and not (user.is_staff or user.is_superuser):
            raise PermissionDenied("You don't have permission to update this course")
        
        if title is not None:
            course.title = title
        
        if description is not None:
            course.description = description
        
        if price is not None:
            course.price = price
        
        if status is not None:
            course.status = status
        
        course.save()
        
        return UpdateCourse(success=True, course=course)

class CreateModule(graphene.Mutation):
    module = graphene.Field(ModuleType)
    success = graphene.Boolean()
    
    class Arguments:
        course_id = graphene.ID(required=True)
        title = graphene.String(required=True)
        description = graphene.String()
        order = graphene.Int()
    
    @login_required
    def mutate(self, info, course_id, title, description=None, order=None):
        user = info.context.user
        
        try:
            course = Course.objects.get(pk=course_id)
        except Course.DoesNotExist:
            return CreateModule(success=False, module=None)
        
        # Only the instructor or staff can create modules
        if course.instructor.id != user.id and not (user.is_staff or user.is_superuser):
            raise PermissionDenied("You don't have permission to create modules for this course")
        
        # If order is not provided, add to the end
        if order is None:
            order = Module.objects.filter(course=course).count() + 1
        
        module = Module(
            course=course,
            title=title,
            description=description or "",
            order=order
        )
        module.save()
        
        return CreateModule(success=True, module=module)

class CreateMaterial(graphene.Mutation):
    material = graphene.Field(MaterialType)
    success = graphene.Boolean()
    
    class Arguments:
        module_id = graphene.ID(required=True)
        title = graphene.String(required=True)
        description = graphene.String()
        type = MaterialTypeEnum(required=True)
        content = graphene.String()
        url = graphene.String()
        order = graphene.Int()
    
    @login_required
    def mutate(self, info, module_id, title, type, description=None, content=None, url=None, order=None):
        user = info.context.user
        
        try:
            module = Module.objects.get(pk=module_id)
        except Module.DoesNotExist:
            return CreateMaterial(success=False, material=None)
        
        # Only the instructor or staff can create materials
        if module.course.instructor.id != user.id and not (user.is_staff or user.is_superuser):
            raise PermissionDenied("You don't have permission to create materials for this module")
        
        # If order is not provided, add to the end
        if order is None:
            order = Material.objects.filter(module=module).count() + 1
        
        material = Material(
            module=module,
            title=title,
            description=description or "",
            type=type,
            content=content or "",
            url=url or "",
            order=order
        )
        material.save()
        
        return CreateMaterial(success=True, material=material)

class EnrollInCourse(graphene.Mutation):
    enrollment = graphene.Field(EnrollmentType)
    success = graphene.Boolean()
    
    class Arguments:
        course_id = graphene.ID(required=True)
    
    @login_required
    def mutate(self, info, course_id):
        user = info.context.user
        
        try:
            course = Course.objects.get(pk=course_id)
        except Course.DoesNotExist:
            return EnrollInCourse(success=False, enrollment=None)
        
        # Check if course is published
        if course.status != CourseStatus.PUBLISHED:
            raise PermissionDenied("This course is not available for enrollment")
        
        # Check if already enrolled
        if course.students.filter(id=user.id).exists():
            enrollment = Enrollment.objects.get(course=course, student=user)
            return EnrollInCourse(success=True, enrollment=enrollment)
        
        # Enroll the user
        course.students.add(user)
        enrollment = Enrollment.objects.create(course=course, student=user)
        
        return EnrollInCourse(success=True, enrollment=enrollment)

class SubmitTask(graphene.Mutation):
    submission = graphene.Field(TaskSubmissionType)
    success = graphene.Boolean()
    
    class Arguments:
        task_id = graphene.ID(required=True)
        content = graphene.String()
    
    @login_required
    def mutate(self, info, task_id, content=None):
        user = info.context.user
        
        try:
            task = Task.objects.get(pk=task_id)
        except Task.DoesNotExist:
            return SubmitTask(success=False, submission=None)
        
        # Check if enrolled in the course
        if not task.course.students.filter(id=user.id).exists():
            raise PermissionDenied("You must be enrolled in this course to submit tasks")
        
        # Check if already submitted
        existing_submission = TaskSubmission.objects.filter(task=task, student=user).first()
        if existing_submission:
            existing_submission.content = content or ""
            existing_submission.save()
            return SubmitTask(success=True, submission=existing_submission)
        
        # Create new submission
        submission = TaskSubmission(
            task=task,
            student=user,
            content=content or ""
        )
        submission.save()
        
        return SubmitTask(success=True, submission=submission)

class GradeTaskSubmission(graphene.Mutation):
    submission = graphene.Field(TaskSubmissionType)
    success = graphene.Boolean()
    
    class Arguments:
        submission_id = graphene.ID(required=True)
        grade = graphene.Float(required=True)
        feedback = graphene.String()
    
    @login_required
    def mutate(self, info, submission_id, grade, feedback=None):
        user = info.context.user
        
        try:
            submission = TaskSubmission.objects.get(pk=submission_id)
        except TaskSubmission.DoesNotExist:
            return GradeTaskSubmission(success=False, submission=None)
        
        # Only the instructor or staff can grade submissions
        if submission.task.course.instructor.id != user.id and not (user.is_staff or user.is_superuser):
            raise PermissionDenied("You don't have permission to grade this submission")
        
        submission.grade = grade
        submission.feedback = feedback or ""
        submission.save()
        
        return GradeTaskSubmission(success=True, submission=submission)

class Mutation(graphene.ObjectType):
    create_course = CreateCourse.Field()
    update_course = UpdateCourse.Field()
    create_module = CreateModule.Field()
    create_material = CreateMaterial.Field()
    enroll_in_course = EnrollInCourse.Field()
    submit_task = SubmitTask.Field()
    grade_task_submission = GradeTaskSubmission.Field() 
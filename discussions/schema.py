import graphene
from graphene_django import DjangoObjectType
from graphql_jwt.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import models

from .models import DiscussionPost, DiscussionReply
from courses.models import Course, CourseStatus

class DiscussionPostType(DjangoObjectType):
    class Meta:
        model = DiscussionPost
        fields = '__all__'
    
    reply_count = graphene.Int()
    
    def resolve_reply_count(self, info):
        return self.reply_count

class DiscussionReplyType(DjangoObjectType):
    class Meta:
        model = DiscussionReply
        fields = '__all__'

class Query(graphene.ObjectType):
    discussion_posts = graphene.List(
        DiscussionPostType,
        course_id=graphene.ID(required=True),
        search=graphene.String(),
        skip=graphene.Int(),
        limit=graphene.Int()
    )
    discussion_post = graphene.Field(DiscussionPostType, id=graphene.ID(required=True))
    
    discussion_replies = graphene.List(
        DiscussionReplyType,
        post_id=graphene.ID(required=True),
        skip=graphene.Int(),
        limit=graphene.Int()
    )
    
    @login_required
    def resolve_discussion_posts(self, info, course_id, search=None, skip=None, limit=None):
        user = info.context.user
        
        try:
            course = Course.objects.get(pk=course_id)
        except Course.DoesNotExist:
            return DiscussionPost.objects.none()
        
        # Check permissions
        if course.status != CourseStatus.PUBLISHED:
            if user.is_student and not course.students.filter(id=user.id).exists():
                return DiscussionPost.objects.none()
            if user.is_instructor and course.instructor.id != user.id and not (user.is_staff or user.is_superuser):
                return DiscussionPost.objects.none()
        
        qs = DiscussionPost.objects.filter(course_id=course_id)
        
        if search:
            qs = qs.filter(
                models.Q(topic__icontains=search) |
                models.Q(content__icontains=search)
            )
        
        if skip:
            qs = qs[skip:]
        
        if limit:
            qs = qs[:limit]
        
        return qs
    
    @login_required
    def resolve_discussion_post(self, info, id):
        user = info.context.user
        
        try:
            post = DiscussionPost.objects.get(pk=id)
        except DiscussionPost.DoesNotExist:
            return None
        
        course = post.course
        
        # Check permissions
        if course.status != CourseStatus.PUBLISHED:
            if user.is_student and not course.students.filter(id=user.id).exists():
                return None
            if user.is_instructor and course.instructor.id != user.id and not (user.is_staff or user.is_superuser):
                return None
        
        return post
    
    @login_required
    def resolve_discussion_replies(self, info, post_id, skip=None, limit=None):
        user = info.context.user
        
        try:
            post = DiscussionPost.objects.get(pk=post_id)
        except DiscussionPost.DoesNotExist:
            return DiscussionReply.objects.none()
        
        course = post.course
        
        # Check permissions
        if course.status != CourseStatus.PUBLISHED:
            if user.is_student and not course.students.filter(id=user.id).exists():
                return DiscussionReply.objects.none()
            if user.is_instructor and course.instructor.id != user.id and not (user.is_staff or user.is_superuser):
                return DiscussionReply.objects.none()
        
        qs = DiscussionReply.objects.filter(post_id=post_id)
        
        if skip:
            qs = qs[skip:]
        
        if limit:
            qs = qs[:limit]
        
        return qs

class CreateDiscussionPost(graphene.Mutation):
    post = graphene.Field(DiscussionPostType)
    success = graphene.Boolean()
    
    class Arguments:
        course_id = graphene.ID(required=True)
        topic = graphene.String(required=True)
        content = graphene.String(required=True)
    
    @login_required
    def mutate(self, info, course_id, topic, content):
        user = info.context.user
        
        try:
            course = Course.objects.get(pk=course_id)
        except Course.DoesNotExist:
            return CreateDiscussionPost(success=False, post=None)
        
        # Check if the user is enrolled in the course or is the instructor
        if not (course.students.filter(id=user.id).exists() or 
                course.instructor.id == user.id or 
                user.is_staff or user.is_superuser):
            raise PermissionDenied("You must be enrolled in this course or be the instructor to create discussion posts")
        
        post = DiscussionPost(
            course=course,
            author=user,
            topic=topic,
            content=content
        )
        post.save()
        
        return CreateDiscussionPost(success=True, post=post)

class ReplyToDiscussionPost(graphene.Mutation):
    reply = graphene.Field(DiscussionReplyType)
    success = graphene.Boolean()
    
    class Arguments:
        post_id = graphene.ID(required=True)
        content = graphene.String(required=True)
    
    @login_required
    def mutate(self, info, post_id, content):
        user = info.context.user
        
        try:
            post = DiscussionPost.objects.get(pk=post_id)
        except DiscussionPost.DoesNotExist:
            return ReplyToDiscussionPost(success=False, reply=None)
        
        course = post.course
        
        # Check if the user is enrolled in the course or is the instructor
        if not (course.students.filter(id=user.id).exists() or 
                course.instructor.id == user.id or 
                user.is_staff or user.is_superuser):
            raise PermissionDenied("You must be enrolled in this course or be the instructor to reply to discussion posts")
        
        reply = DiscussionReply(
            post=post,
            author=user,
            content=content
        )
        reply.save()
        
        return ReplyToDiscussionPost(success=True, reply=reply)

class Mutation(graphene.ObjectType):
    create_discussion_post = CreateDiscussionPost.Field()
    reply_to_discussion_post = ReplyToDiscussionPost.Field() 
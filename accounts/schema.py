import graphene
from graphene_django import DjangoObjectType
from django.contrib.auth import get_user_model
from graphql_jwt.decorators import login_required
import graphql_jwt
from graphene_file_upload.scalars import Upload

from .models import User, UserProfile, UserRole

class UserType(DjangoObjectType):
    class Meta:
        model = User
        exclude = ('password',)
    
    full_name = graphene.String()
    role_display = graphene.String()
    
    def resolve_full_name(self, info):
        return self.full_name
    
    def resolve_role_display(self, info):
        return self.get_role_display()

class UserProfileType(DjangoObjectType):
    class Meta:
        model = UserProfile
        fields = '__all__'

class UserRoleEnum(graphene.Enum):
    STUDENT = UserRole.STUDENT
    INSTRUCTOR = UserRole.INSTRUCTOR
    ADMIN = UserRole.ADMIN

class Query(graphene.ObjectType):
    me = graphene.Field(UserType)
    user = graphene.Field(UserType, id=graphene.ID(required=True))
    users = graphene.List(
        UserType,
        role=UserRoleEnum(),
        search=graphene.String(),
        skip=graphene.Int(),
        limit=graphene.Int()
    )
    
    @login_required
    def resolve_me(self, info):
        return info.context.user
    
    @login_required
    def resolve_user(self, info, id):
        user = info.context.user
        
        if user.is_staff or user.is_superuser:
            return User.objects.get(pk=id)
        elif str(user.id) == id:
            return user
        return None
    
    @login_required
    def resolve_users(self, info, role=None, search=None, skip=None, limit=None):
        user = info.context.user
        
        # Only staff and instructors can list users
        if not (user.is_staff or user.is_superuser or user.is_instructor):
            return User.objects.none()
        
        qs = User.objects.all()
        
        if role:
            qs = qs.filter(role=role)
        
        if search:
            qs = qs.filter(
                models.Q(email__icontains=search) |
                models.Q(first_name__icontains=search) |
                models.Q(last_name__icontains=search)
            )
        
        if skip:
            qs = qs[skip:]
        
        if limit:
            qs = qs[:limit]
        
        return qs

class RegisterUser(graphene.Mutation):
    user = graphene.Field(UserType)
    success = graphene.Boolean()
    message = graphene.String()
    
    class Arguments:
        email = graphene.String(required=True)
        username = graphene.String(required=True)
        password = graphene.String(required=True)
        first_name = graphene.String()
        last_name = graphene.String()
    
    def mutate(self, info, email, username, password, first_name=None, last_name=None):
        # Check if user with email or username exists
        if User.objects.filter(email=email).exists():
            return RegisterUser(success=False, message="Email already in use")
        
        if User.objects.filter(username=username).exists():
            return RegisterUser(success=False, message="Username already in use")
        
        user = User(
            username=username,
            email=email,
            first_name=first_name or "",
            last_name=last_name or "",
            role=UserRole.STUDENT
        )
        user.set_password(password)
        user.save()
        
        return RegisterUser(success=True, user=user, message="Registration successful")

class UpdateUserProfile(graphene.Mutation):
    profile = graphene.Field(UserProfileType)
    success = graphene.Boolean()
    
    class Arguments:
        bio = graphene.String()
        phone_number = graphene.String()
        address = graphene.String()
        avatar = Upload()
    
    @login_required
    def mutate(self, info, bio=None, phone_number=None, address=None, avatar=None):
        user = info.context.user
        profile = user.profile
        
        if bio is not None:
            profile.bio = bio
        
        if phone_number is not None:
            profile.phone_number = phone_number
        
        if address is not None:
            profile.address = address
            
        if avatar is not None:
            # Delete old avatar if exists
            if profile.avatar:
                profile.avatar.delete()
            profile.avatar = avatar
        
        profile.save()
        
        return UpdateUserProfile(success=True, profile=profile)

class Mutation(graphene.ObjectType):
    register_user = RegisterUser.Field()
    update_profile = UpdateUserProfile.Field()
    
    # JWT Authentication
    token_auth = graphql_jwt.ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field() 
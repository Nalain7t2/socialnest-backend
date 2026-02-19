from django.conf import settings
from rest_framework import serializers
from .models import Post, Comment, Like , Profile
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from .validators import validate_profile_image
from django.db import transaction


#  use for user validate by username or email both of them and it's store both jwt tokens
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):

    def validate(self, attrs):
        identifier = attrs.get("username")
        password = attrs.get("password")

        if not identifier or not password:
            raise serializers.ValidationError("Username/email and password required")

        # Find user by email OR username
        user = (
            User.objects.filter(email=identifier).first()
            or User.objects.filter(username=identifier).first()
        )

        if not user:
            raise serializers.ValidationError("Invalid credentials")

        # Authenticate properly
        user = authenticate(
            request=self.context.get("request"),
            username=user.username,
            password=password,
        )

        if not user:
            raise serializers.ValidationError("Invalid credentials")

        data = super().validate({
            "username": user.username,
            "password": password
        })

        data["username"] = user.username
        return data

class CommentSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Comment
        fields = '__all__'   

class PostsSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    user_name = serializers.CharField(source="user.username", read_only=True)
    image = serializers.ImageField(required=False)
    user_avatar = serializers.SerializerMethodField()

    likes_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    comments = CommentSerializer(many=True, read_only= True)
    class Meta:
        model = Post
        fields = '__all__'
        read_only_fields = ('created_at', "user")

    def get_user_avatar(self, obj):
        profile = obj.user.profile
        if profile.avatar:
            request = self.context.get('request')
            return request.build_absolute_uri(profile.avatar.url)
        return None    

    def get_likes_count(self, obj):
        return obj.likes.count()    
    
    def get_is_liked(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False
    
    def get_image(self, obj):
        request = self.context.get("request")
        if obj.image:
            return request.build_absolute_uri(obj.image.url)
        return None
    
    def get_user_avatar(self, obj):
        try:
            if obj.user.profile.avatar:
                request = self.context.get('request')
                if request:
                    return request.build_absolute_uri(obj.user.profile.avatar.url)
                return obj.user.profile.avatar.url
        except:
            pass
        return None


class ProfileSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    is_following = serializers.SerializerMethodField()
    followers_count = serializers.SerializerMethodField()
    joined_date = serializers.DateTimeField(source='user.date_joined', read_only=True)
    avatar = serializers.ImageField(required=False, allow_null=True)
    bio = serializers.CharField(required=False, allow_blank=True)  
    email = serializers.EmailField(source='user.email', read_only=True)  
    

    class Meta:
        model = Profile
        fields = [
            'id',
            'user_id',
            'username',
            'avatar',
            'email',  
            'bio',   
            'joined_date',
            'is_following',
            'followers_count',
        ]

    def get_avatar(self, obj):
        try:
            if obj.avatar:
                request = self.context.get('request')
                if request:
                    return request.build_absolute_uri(obj.avatar.url)
                else:
                    return obj.avatar.url
        except:
            pass
        return None   
    

    def get_is_following(self, obj):
        """Check if current user is following this profile"""
        try:
            request = self.context.get('request')
            
            if not request or not request.user.is_authenticated:
                return False

            current_user = request.user
            current_profile = current_user.profile
            return obj.followers.filter(id=current_profile.id).exists()
            
        except Exception as e:
            print(f"ERROR in get_is_following: {e}")
            return False

    def get_followers_count(self, obj):
        """Get number of followers for this profile"""
        try:
            return obj.followers.count()
        except:
            return 0
class UserFollowSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(source='profile', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'profile']

class FollowActionSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(required=True)
    action = serializers.ChoiceField(
        choices=['follow', 'unfollow'],
        required=True
    )       

class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer( read_only=True)
    avatar = serializers.SerializerMethodField()
    bio = serializers.CharField(source='profile.bio', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'profile', 'avatar', 'bio']
    
    def get_avatar(self, obj):
        if hasattr(obj, 'profile') and obj.profile.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.profile.avatar.url)
            return obj.profile.avatar.url
        return None

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        min_length=8,
        style={'input_type': 'password'},
        error_messages={
            'min_length': 'Password must be at least 8 characters.',
            'required': 'Password is required.'
        }
    )
    confirm_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        error_messages={
            'required': 'Confirm password is required.'
        }
    )
    profile_image = serializers.ImageField(
        write_only=True,
        required=False,
        allow_null=True,
        validators=[validate_profile_image]
    )
    bio = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'confirm_password', 'profile_image', 'bio']
        extra_kwargs = {
            'username': {
                'min_length': 3,
                'max_length': 30,
                'error_messages': {
                    'min_length': 'Username must be at least 3 characters.',
                    'max_length': 'Username must be less than 30 characters.',
                    'required': 'Username is required.'
                }
            },
            'email': {
                'required': True,
                'error_messages': {
                    'required': 'Email is required.',
                    'invalid': 'Enter a valid email address.'
                }
            }
        }
    
    def validate_username(self, value):
        value = value.strip()
        if not value.replace('_', '').isalnum():
            raise serializers.ValidationError('Username can only contain letters, numbers and underscores.')
        
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError('Username already exists.')
        
        return value.lower()
    
    def validate_email(self, value):
        value = value.strip().lower()
        if not value:
            raise serializers.ValidationError('Email is required.')
        
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('Email already exists.')
        
        return value
    
    def validate(self, data):
        password = data.get('password')
        confirm_password = data.get('confirm_password')
        
        if password != confirm_password:
            raise serializers.ValidationError({
                'confirm_password': 'Passwords do not match.'
            })
        
        # Check password strength
        errors = []
        
        if len(password) < 8:
            errors.append('Password must be at least 8 characters.')
        
        if not any(char.isdigit() for char in password):
            errors.append('Password must contain at least one digit.')
        
        if not any(char.isupper() for char in password):
            errors.append('Password must contain at least one uppercase letter.')
        
        if not any(char.islower() for char in password):
            errors.append('Password must contain at least one lowercase letter.')
        
        if errors:
            raise serializers.ValidationError({'password': errors})
        
        return data
    # transaction.atomic ensures database consistency by rolling back all operations if any step fails.
    @transaction.atomic
    def create(self, validated_data):
        profile_image = validated_data.pop('profile_image', None)
        bio = validated_data.pop('bio', '')
        validated_data.pop('confirm_password', None)
        
        # Create user
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
        )
        
        profile, created = Profile.objects.get_or_create(user=user)
        profile.bio = bio  
        profile.save()
        
        if profile_image:
            # Delete old avatar if exists
            if profile.avatar:
                profile.avatar.delete(save=False)
            profile.avatar = profile_image
            profile.save()
        
        return user

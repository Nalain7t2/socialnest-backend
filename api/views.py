from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .models import Post, Like, Comment, Profile
from django.db import models
from django.contrib.auth import authenticate
from .serializers import PostsSerializer , CommentSerializer, UserSerializer,  RegisterSerializer, ProfileSerializer, UserFollowSerializer, FollowActionSerializer
from rest_framework import status, generics
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.authtoken.models import Token
from django.db.models import Q
from django.contrib.auth.models import User
from .pagination import PostPagination
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

# Create your views here.


@api_view(['POST'])
@permission_classes([AllowAny])
def login_api(requets):
    identifier = requets.data.get('identifier')
    password = requets.data.get('password')

    if not identifier or not password:
        return Response(
            { "error": "All fields are required"},
            status=status.HTTP_400_BAD_REQUEST
        )
    user = User.objects.filter(
        models.Q(username=identifier) | models.Q(email=identifier)
    ).first()

    if user:
        user = authenticate(username = user.username, password = password)
        if user:
            refresh = RefreshToken.for_user(user)
            return Response(
                {
                  "refresh": str(refresh),
                  "access": str(refresh.access_token),  
                  "message": "Login Sucessfully",
                 }
            )
    return Response({"error": "Invalid credidential"}, status=status.HTTP_400_BAD_REQUEST)    

@api_view(['POST'])
@permission_classes([AllowAny])
def forget_password(request):
    email = request.data.get("email")

    if not email:
        return Response(
            {"error": "Email is required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response(
            {"error": "Email not found"},
            status=status.HTTP_400_BAD_REQUEST
        )

    new_password = get_random_string(8)
    user.set_password(new_password)
    user.save()

    send_mail(
        'Password reset',
        f"Your new password is {new_password}",
        'noreply@yourapp.com',
        [email],
        fail_silently=False
    )

    return Response(
        {"message": "New password sent to your email"},
        status=status.HTTP_200_OK
    )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """
    Change password for authenticated user
    Requires: old_password, new_password, confirm_password
    """
    old_password = request.data.get('old_password')
    new_password = request.data.get('new_password')
    confirm_password = request.data.get('confirm_password')
    
    # Validation - All fields required
    if not old_password or not new_password or not confirm_password:
        return Response({
            'error': 'All fields are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Validation - New passwords match
    if new_password != confirm_password:
        return Response({
            'error': 'New passwords do not match'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Validation - Password length
    if len(new_password) < 8:
        return Response({
            'error': 'Password must be at least 8 characters long'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Get current user
    user = request.user
    
    # Check old password
    if not user.check_password(old_password):
        return Response({
            'error': 'Current password is incorrect'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Check if new password is same as old
    if old_password == new_password:
        return Response({
            'error': 'New password must be different from current password'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Set new password
    user.set_password(new_password)
    user.save()
    
    try:
        send_mail(
            'Password Changed Successfully',
            f'''Hello {user.username},

Your password has been changed successfully.

If you did not make this change, please contact support immediately and reset your password.

Best regards,
SocialNest Team''',
            settings.DEFAULT_FROM_EMAIL or 'noreply@socialnest.com',
            [user.email],
            fail_silently=True  # Don't fail if email doesn't send
        )
    except Exception as e:
        # print(f"Password change email failed: {e}")
    
        return Response({
        'message': 'Password changed successfully'
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password_without_old(request):
    """
    Change password without old password (for verified users/admin)
    Requires: new_password, confirm_password
    """
    new_password = request.data.get('new_password')
    confirm_password = request.data.get('confirm_password')
    
    if not new_password or not confirm_password:
        return Response({
            'error': 'All fields are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if new_password != confirm_password:
        return Response({
            'error': 'Passwords do not match'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if len(new_password) < 8:
        return Response({
            'error': 'Password must be at least 8 characters long'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    user = request.user
    user.set_password(new_password)
    user.save()
    
    return Response({
        'message': 'Password changed successfully'
    }, status=status.HTTP_200_OK)

def get_or_create_user_from_google_token(token):
    try:
        idinfo = id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID
        )

        email = idinfo.get("email")
        name = idinfo.get("name")

        user, created = User.objects.get_or_create(
            email=email,
            defaults={"username": email, "first_name": name}
        )

        return user

    except ValueError:
        return None

@api_view(["POST"])
@permission_classes([AllowAny])
def google_login(request):
    token = request.data.get("token")

    user = get_or_create_user_from_google_token(token)
    if not user:
        return Response({"error": "Invalid Google token"}, status=400)

    refresh = RefreshToken.for_user(user)

    return Response({
        "access": str(refresh.access_token),
        "refresh": str(refresh)
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user(request):
    """Get current user with profile"""
    serializer = UserSerializer(request.user, context={'request': request})
    return Response(serializer.data)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticatedOrReadOnly])
def post_api(request):

    if request.method == 'GET':
        search = request.GET.get("search", "")

        posts = Post.objects.filter(
            Q(title__icontains=search) |
            Q(content__icontains=search)
        ).order_by("-id")

        paginator = PostPagination()
        paginated_posts = paginator.paginate_queryset(posts, request)
        serializer = PostsSerializer(paginated_posts, many=True, context ={"request": request})

        return paginator.get_paginated_response(serializer.data)

    elif request.method == 'POST':
        serializer = PostsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_post(request):
    search = request.GET.get("search", "")

    posts = Post.objects.filter(user = request.user).filter(
        Q(title__icontains=search) |
        Q(content__icontains=search)
    ).order_by("-id")    
    paginator = PostPagination()
    paginated_posts = paginator.paginate_queryset(posts, request)
    serializer = PostsSerializer(paginated_posts, many=True)

    return paginator.get_paginated_response(serializer.data)

@api_view(['PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def post_detail(request, post_id):
    try:
        post = Post.objects.get(id=post_id, user=request.user)
    except Post.DoesNotExist:
        return Response(
            {"error": "Post not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    if request.method == "PATCH":
        serializer = PostsSerializer(post, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    if request.method == "DELETE":
        post.delete()
        return Response(
            {"message": "Post deleted successfully"},
            status=status.HTTP_200_OK
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def LikePostView(request, post_id):
    post = Post.objects.get(id=post_id)

    like, created = Like.objects.get_or_create(
        user=request.user,
        post=post
    )

    if not created:
        like.delete()
        return Response({"liked": False})

    return Response({"liked": True})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def CommentCreateView(request, post_id):
    post = Post.objects.get(id=post_id)

    text = request.data.get("text")

    if not text or text.strip() == "":
        return Response(
            {"error": "Comment text is required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    comment = Comment.objects.create(
        user=request.user,
        post=post,
        text=text
    )

    serializer = CommentSerializer(comment)
    return Response(serializer.data, status=status.HTTP_201_CREATED)
        
@csrf_exempt    
@api_view(['POST'])
@permission_classes([AllowAny])
def RegisterView(request):
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()

    refresh = RefreshToken.for_user(user)

    user_data = UserSerializer(user, context={'request': request}).data

    return Response({
        'user': user_data,
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'message': 'User registered successfully'
    }, status=status.HTTP_201_CREATED)
    

@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_profile(request):

    profile = request.user.profile

    serializer = ProfileSerializer(
        profile,
        data=request.data,
        partial=True,
        context={'request': request}
    )

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def suggestions_to_follow(request):
    """Get suggestions for users to follow"""
    # print("\n" + "="*60)
    # print("SUGGESTIONS API CALLED")
    # print(f"Request user: {request.user.username} (ID: {request.user.id})")
    
    try:
        current_user = request.user
        current_profile = current_user.profile
        
        # print(f"Current profile ID: {current_profile.id}")
        
        following_profiles = current_profile.followers.all()
        # print(f"\n{current_user.username} is currently following {following_profiles.count()} users:")
        for profile in following_profiles:
            # print(f"  - {profile.user.username} (Profile ID: {profile.id}, User ID: {profile.user.id})")
        
        # Get IDs of users already followed
         following_ids = current_profile.followers.values_list('id', flat=True)
        #  print(f"\nFollowing profile IDs: {list(following_ids)}")
        
        # Get all other profiles
        #  all_other_profiles = Profile.objects.exclude(user=current_user)
        #  print(f"\nTotal other profiles: {all_other_profiles.count()}")
        
         suggestions = Profile.objects.exclude(
            user=current_user
        ).exclude(
            id__in=following_ids
        ).order_by('?')[:5]
        
        # print(f"\nSelected {suggestions.count()} suggestions:")
        for profile in suggestions:
            # Check is_following manually
            is_following = current_profile.followers.filter(id=profile.id).exists()
            # print(f"  - {profile.user.username} (User ID: {profile.user.id}): is_following={is_following}")
        
        # print(f"\nSerializing suggestions with context:")
        # print(f"  Request in context: {'request' in locals()}")
        
        serializer = ProfileSerializer(
            suggestions, 
            many=True,
            context={'request': request}  
        )
        
        # print(f"\nSerialized data preview:")
        for i, data in enumerate(serializer.data[:3]):
            # print(f"  [{i}] {data.get('username')}: is_following={data.get('is_following')}")
        
        # print("\n" + "="*60)
        
         return Response(serializer.data)
        
    except Exception as e:
        # print(f"ERROR in suggestions_to_follow: {e}")
        import traceback
        traceback.print_exc()
        # print("="*60)
        
        return Response(
            {'error': 'Could not load suggestions'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_users(request):
    """
    Search users by username
    """
    query = request.query_params.get('q', '').strip()

    if not query:
        return Response([])

    current_profile = request.user.profile

    # IDs of users already followed
    following_ids = current_profile.followers.values_list('id', flat=True)

    users = Profile.objects.filter(
        user__username__icontains=query
    ).exclude(
        user=request.user
    ).exclude(
        id__in=following_ids
    )[:10]

    serializer = ProfileSerializer(
        users,
        many=True,
        context={'request': request}
    )

    return Response(serializer.data)    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def follow_user(request):
    user_id = request.data.get('user_id')
    action = request.data.get('action')

    if not user_id or not action:
        return Response(
            {'error': 'user_id and action are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        target_user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response(
            {'error': 'User not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    current_profile = request.user.profile
    target_profile = target_user.profile

    # print(f"\n{'='*60}")
    # print(f"FOLLOW ACTION: {action}")
    # print(f"Current user: {request.user.username} (Profile ID: {current_profile.id})")
    # print(f"Target user: {target_user.username} (Profile ID: {target_profile.id})")
    
    if action == 'follow':
        # CORRECT: Current user follows target user
        # So add current_profile to target_profile's followers
        # This means: target_profile.followers.add(current_profile)
        
        # print(f"Before follow - Who follows target? (target's followers): {list(target_profile.followers.values_list('user__username', flat=True))}")
        # print(f"Before follow - Who current follows? (current's following): {list(current_profile.following.values_list('user__username', flat=True))}")
        
        # Add current_profile to target's followers
        target_profile.followers.add(current_profile)
        
        is_following = True
        # print(f"After follow - Who follows target? (target's followers): {list(target_profile.followers.values_list('user__username', flat=True))}")
        # print(f"After follow - Who current follows? (current's following): {list(current_profile.following.values_list('user__username', flat=True))}")

    elif action == 'unfollow':
        # print(f"Before unfollow - Who follows target? (target's followers): {list(target_profile.followers.values_list('user__username', flat=True))}")
        # print(f"Before unfollow - Who current follows? (current's following): {list(current_profile.following.values_list('user__username', flat=True))}")
        
        # Remove current_profile from target's followers
        target_profile.followers.remove(current_profile)
        
        is_following = False
        # print(f"After unfollow - Who follows target? (target's followers): {list(target_profile.followers.values_list('user__username', flat=True))}")
        # print(f"After unfollow - Who current follows? (current's following): {list(current_profile.following.values_list('user__username', flat=True))}")

    else:
        return Response(
            {'error': 'Invalid action'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # print(f"{'='*60}")
    
    return Response({
        'success': True,
        'is_following': is_following,
        'followers_count': target_profile.followers.count(),
        'following_count': current_profile.following.count()  
    })
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_followers(request):
    """Get users who follow the current user with search"""
    try:
        profile = request.user.profile
        search_query = request.GET.get('search', '').strip()
        
        # People who follow current user
        followers = profile.followers.all()
        
        # Apply search if provided
        if search_query:
            followers = followers.filter(
                Q(user__username__icontains=search_query) |
                Q(user__email__icontains=search_query)
            )
        
        # Pagination
        page = int(request.GET.get('page', 1))
        page_size = 10
        start = (page - 1) * page_size
        end = start + page_size
        
        total_count = followers.count()
        paginated_followers = followers[start:end]
        
        serializer = ProfileSerializer(
            paginated_followers, 
            many=True,
            context={'request': request}
        )
        
        return Response({
            "followers_count": total_count,
            "followers": serializer.data,
            "has_next": end < total_count,
            "has_previous": page > 1,
            "current_page": page,
            "total_pages": (total_count + page_size - 1) // page_size
        })
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_following(request):
    """Get users that the current user is following with search"""
    try:
        profile = request.user.profile
        search_query = request.GET.get('search', '').strip()
        
        # People that current user follows
        following = profile.following.all()
        
        # Apply search 
        if search_query:
            following = following.filter(
                Q(user__username__icontains=search_query) |
                Q(user__email__icontains=search_query)
            )
        
        # Pagination
        page = int(request.GET.get('page', 1))
        page_size = 10
        start = (page - 1) * page_size
        end = start + page_size
        
        total_count = following.count()
        paginated_following = following[start:end]
        
        serializer = ProfileSerializer(
            paginated_following, 
            many=True,
            context={'request': request}
        )
        
        return Response({
            "following_count": total_count,
            "following": serializer.data,
            "has_next": end < total_count,
            "has_previous": page > 1,
            "current_page": page,
            "total_pages": (total_count + page_size - 1) // page_size
        })
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
@api_view(['GET'])
def user_profile(request, username):
    """Get user profile with follow status"""
    try:
        user = User.objects.get(username=username)
        profile = user.profile
        
        serializer = ProfileSerializer(
            profile,
            context={'request': request}
        )
        
        return Response(serializer.data)
    except User.DoesNotExist:
        return Response(
            {'error': 'User not found'},
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def delete_account(request):
    user = request.user
    password = request.data.get("password")

    if not password:
        return Response(
            {"error": "Password is required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Verify password
    if not user.check_password(password):
        return Response(
            {"error": "Incorrect password"},
            status=status.HTTP_400_BAD_REQUEST
        )

    user.delete()

    return Response(
        {"message": "Account deleted successfully"},
        status=status.HTTP_204_NO_CONTENT
    )

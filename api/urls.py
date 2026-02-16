from django.urls import path
from .views import post_api, post_detail, login_api, RegisterView, current_user, my_post, google_login, forget_password, LikePostView, CommentCreateView, suggestions_to_follow, follow_user, get_followers,get_following, user_profile, delete_account, search_users, change_password, change_password_without_old, update_profile
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

urlpatterns = [
   path('Post/', post_api, name='Post_api'),
   path('Post/<int:post_id>/', post_detail, name='Post_detail'),
   path('Post/<int:post_id>/like/', LikePostView, name='Post_likes'),
   path('Post/<int:post_id>/comment/', CommentCreateView, name='Post_comments'),
   path('my-posts/', my_post, name='my_posts'),
   path('login/', login_api, name='login_api'),
   path('register/', RegisterView, name='register'),
   path('current_user/', current_user, name='current_user'),
   path('token/', CustomTokenObtainPairView.as_view()),
   path('token/refresh/', TokenRefreshView.as_view()),
   path('forget-password/', forget_password, name='forget-password'),
   path('google-login/', google_login, name='google-login'),
   path('suggestions/', suggestions_to_follow, name='suggestions'),
   path('follow/', follow_user, name='follow_user'),
   path('followers/', get_followers, name='get_followers'),
   path('following/', get_following, name='get_following'),
   path('profile/<str:username>/', user_profile, name='user_profile'),
   path('delete-account/', delete_account, name='delete_account' ),
   path('users/search/', search_users, name='search_user'),
   path('change-password/', change_password, name='change_password'),
   path('change-password-without-old/', change_password_without_old, name='change_password_without_old'),
   path('update-profile/', update_profile, name='update_profile'),
]

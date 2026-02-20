# SocialNest Backend API 🚀

Backend API for SocialNest - a modern social media platform built with Django REST Framework. This API powers user authentication, posts, comments, likes, follow system, and more.

## 🛠️ Tech Stack

- **Framework:** Django 4.2 / Django REST Framework
- **Database:** PostgreSQL (Production) / SQLite3 (Development)
- **Authentication:** JWT (Simple JWT) + Google OAuth
- **Deployment:** Render
- **Other Tools:** Whitenoise, CORS headers, Django cors headers

## ✨ Features

### 👤 User Management
- User registration with email & username
- JWT authentication (access & refresh tokens)
- Google OAuth integration
- Password reset via email
- Profile management with bio & avatar
- Delete account functionality

### 📱 Social Features
- Create, read, update, delete posts
- Like/unlike posts
- Comment on posts
- Follow/unfollow users
- User suggestions based on follow patterns
- Search users by username/email
- View followers & following lists

### 🔒 Security
- Password hashing with Argon2
- JWT tokens with short expiry (15 min)
- CSRF protection
- CORS configuration
- Rate limiting on auth endpoints
- Secure HTTP headers (HSTS, SSL redirect)

## 📁 Project Structure
backend/
├── api/ # Main app
│ ├── migrations/ # Database migrations
│ ├── init.py
│ ├── admin.py # Admin panel config
│ ├── apps.py # App config
│ ├── models.py # Database models
│ ├── serializers.py # DRF serializers
│ ├── urls.py # API routes
│ ├── validators.py # Custom validators
│ └── views.py # API views
├── backend/ # Project config
│ ├── init.py
│ ├── asgi.py # ASGI config
│ ├── settings.py # Django settings
│ ├── urls.py # Main URLs
│ └── wsgi.py # WSGI config
├── media/ # Uploaded files
├── staticfiles/ # Collected static files
├── manage.py # Django management
├── requirements.txt # Dependencies
└── .env # Environment variables

## 🗄️ Database Models

### User (Django built-in)
- `username`, `email`, `password`
- Extended via Profile model

### Profile
- `user` (One-to-One)
- `bio` (TextField)
- `avatar` (ImageField)
- `followers` (Many-to-Many self)

### Post
- `user` (ForeignKey)
- `content` (TextField)
- `image` (ImageField)
- `created_at` (DateTimeField)
- `likes` (ManyToMany User)
- `comments` (Reverse relation)

### Comment
- `user` (ForeignKey)
- `post` (ForeignKey)
- `text` (TextField)
- `created_at` (DateTimeField)

## 🔌 API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/register/` | Register new user |
| POST | `/api/token/` | Login (get JWT tokens) |
| POST | `/api/token/refresh/` | Refresh access token |
| POST | `/api/google-login/` | Google OAuth login |
| POST | `/api/forget-password/` | Request password reset |
| POST | `/api/change-password/` | Change password |
| POST | `/api/delete-account/` | Delete account |

### Users
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/current_user/` | Get current user |
| GET | `/api/profile/<username>/` | Get user profile |
| GET | `/api/users/search/?q=` | Search users |
| GET | `/api/followers/` | Get followers list |
| GET | `/api/following/` | Get following list |
| POST | `/api/follow/` | Follow/unfollow user |
| GET | `/api/suggestions/` | Get follow suggestions |

### Posts
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/Post/` | List all posts |
| POST | `/api/Post/` | Create new post |
| GET | `/api/Post/<id>/` | Get single post |
| PATCH | `/api/Post/<id>/` | Update post |
| DELETE | `/api/Post/<id>/` | Delete post |
| POST | `/api/Post/<id>/like/` | Like/unlike post |
| POST | `/api/Post/<id>/comment/` | Add comment |
| GET | `/api/my-posts/` | Get current user's posts |

## 🚀 Installation & Setup

### Prerequisites
- Python 3.9+
- pip
- virtualenv (recommended)
- PostgreSQL (optional, SQLite works for development)

### Local Development Setup

```bash
# 1. Clone repository
git clone https://github.com/Nalain7t2/socialnest-backend.git
cd socialnest-backend

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env file
cp .env.example .env
# Edit .env with your settings

# 5. Run migrations
python manage.py migrate

# 6. Create superuser
python manage.py createsuperuser

# 7. Run development server
python manage.py runserver
Django==4.2.0
djangorestframework==3.14.0
djangorestframework-simplejwt==5.2.2
django-cors-headers==4.0.0
psycopg2-binary==2.9.9
dj-database-url==2.1.0
whitenoise==6.6.0
Pillow==10.1.0
python-dotenv==1.0.0
gunicorn==21.2.0
google-auth==2.23.4
google-auth-oauthlib==1.1.0
google-auth-httplib2==0.1.1
requests==2.31.0
python-magic==0.4.27

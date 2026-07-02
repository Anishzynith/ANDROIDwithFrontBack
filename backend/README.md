# Django Backend - ZYbackend Authentication API

## Setup Instructions

### 1. Create Virtual Environment
```bash
python -m venv venv
```

### 2. Activate Virtual Environment
**Windows:**
```bash
venv\Scripts\activate
```

**Mac/Linux:**
```bash
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the backend directory:
```bash
cp .env.example .env
```

Edit `.env` with your configuration:
- `DEBUG`: Set to False in production
- `SECRET_KEY`: Use a strong secret key
- `DATABASE_URL`: PostgreSQL connection string
- `GOOGLE_OAUTH_ID` and `GOOGLE_OAUTH_SECRET`: From Google Cloud Console
- `APPLE_OAUTH_ID`: From Apple Developer Account
- `FRONTEND_URL`: React frontend URL (http://localhost:3000)

### 5. Database Setup (PostgreSQL Required)
Ensure PostgreSQL is running and create a database:
```bash
psql -U postgres
```

```sql
CREATE DATABASE myrun;
```

### 6. Run Migrations
```bash
python manage.py migrate
```

### 7. Create Superuser (Optional)
```bash
python manage.py createsuperuser
```

### 8. Start Development Server
```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000`

## API Endpoints

### Authentication
- `POST /api/auth/login/` - Login with email
- `POST /api/users/signup/` - User registration
- `POST /api/users/signin/` - User login
- `POST /api/users/google_signin/` - Google OAuth signin
- `POST /api/users/apple_signin/` - Apple OAuth signin
- `POST /api/users/logout/` - User logout
- `GET /api/users/profile/` - Get user profile (Authenticated)

### OAuth Providers

#### Google OAuth Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project
3. Enable Google+ API
4. Create OAuth 2.0 credentials (Web application)
5. Add authorized redirect URIs:
   - `http://localhost:8000/`
   - `http://localhost:3000/`
   - `exp://192.168.88.10:8081/--/auth/google`
6. Copy Client ID and Client Secret to `.env`

#### Apple OAuth Setup
1. Go to [Apple Developer Account](https://developer.apple.com)
2. Create App ID with Sign in with Apple capability
3. Create Service ID
4. Create private key for the Service ID
5. Configure in `.env` with:
   - `APPLE_OAUTH_ID`: Service ID
   - `APPLE_OAUTH_TEAM_ID`: Team ID
   - `APPLE_OAUTH_KEY_ID`: Key ID

## Admin Panel
Access Django admin at `http://localhost:8000/admin/` with superuser credentials.

## Troubleshooting

### PostgreSQL Connection Error
Ensure PostgreSQL is running and credentials in `.env` are correct.

### Migration Errors
Try: `python manage.py migrate --fake-initial`

### Port Already in Use
Run on different port: `python manage.py runserver 8001`

## Project Structure
```
backend/
├── config/              # Django configuration
│   ├── settings.py      # Main settings
│   ├── urls.py          # URL routing
│   ├── wsgi.py          # WSGI configuration
│   └── __init__.py
├── users/               # Authentication app
│   ├── models.py        # User models
│   ├── views.py         # API views
│   ├── serializers.py   # DRF serializers
│   ├── urls.py          # App URLs
│   └── admin.py         # Admin configuration
├── manage.py            # Django CLI
├── requirements.txt     # Python dependencies
└── .env.example         # Environment variables template
```

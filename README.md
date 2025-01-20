# User Profile Audit System

A robust user profile management system with complete audit logging capabilities built with FastAPI and PostgreSQL.

## Features

- Complete CRUD operations for user profiles
- Audit logging for all changes
- User state versioning and restoration
- Authentication with JWT
- Comprehensive error handling
- RESTful API design
- Database operations using raw SQL (no ORM)

## Prerequisites

- Python 3.8+
- PostgreSQL
- Docker (optional)

## Setup

1. Clone the repository:
```bash
git clone https://github.com/whisperky/user_pro_audit.git
cd user-profile-audit
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up PostgreSQL:
- Create a database named 'user_profiles'
- Update the DATABASE_URL in .env file with your PostgreSQL credentials

5. Initialize the database:
```bash
python init_db.py
```

6. Run the application:
```bash
uvicorn app.main:app --reload
```

The API will be available at http://localhost:8000

## API Documentation

Once the application is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### User Management
- POST /api/users - Create a new user
- GET /api/users/{user_id} - Get user details
- PUT /api/users/{user_id} - Update user
- DELETE /api/users/{user_id} - Delete user
- GET /api/users - List all users

### Audit
- GET /api/audit/users/{user_id} - Get user audit history
- GET /api/audit/users/{user_id}/version/{version} - Get specific user version
- POST /api/audit/users/{user_id}/restore/{version} - Restore user to specific version

### Authentication
- POST /api/auth/token - Get access token
- POST /api/auth/refresh - Refresh access token

## Testing

Run the test suite:
```bash
pytest
```

## Docker Support

Build and run with Docker:
```bash
docker build -t user-profile-audit .
docker run -p 8000:8000 user-profile-audit
```

## Project Structure

```
user-profile-audit/
├── app/
│   ├── api/
│   │   ├── endpoints/
│   │   │   ├── users.py
│   │   │   ├── audit.py
│   │   │   └── auth.py
│   │   └── dependencies.py
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   └── database.py
│   ├── models/
│   │   └── user.py
│   └── main.py
├── tests/
│   ├── test_users.py
│   └── test_audit.py
├── .env
├── requirements.txt
├── Dockerfile
└── README.md
```

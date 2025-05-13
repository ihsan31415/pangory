# Pangory LMS - Learning Management System

A GraphQL-based Learning Management System built with Django and GraphQL.

## Features

- User management with roles (Student, Instructor, Admin)
- Course creation and management
- Modules and learning materials
- Discussion forums
- Exams and grading
- Certificate generation

## Technologies Used

- Django
- GraphQL (Graphene-Django)
- JWT Authentication
- SQLite (default)

## Setup and Installation

1. Clone the repository:
```bash
git clone https://github.com/your-username/pangory-lms.git
cd pangory-lms
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Migrate database:
```bash
python manage.py migrate
```

4. Create a superuser:
```bash
python manage.py createsuperuser
```

5. Run the development server:
```bash
python manage.py runserver
```

## API Access

- Admin Panel: http://localhost:8000/admin/
- GraphQL API: http://localhost:8000/graphql/

## GraphQL Examples

### Register a new user
```graphql
mutation {
  registerUser(
    email: "student@example.com", 
    username: "student1", 
    password: "securepassword123",
    firstName: "John",
    lastName: "Doe"
  ) {
    success
    message
    user {
      id
      email
      username
      fullName
      role
    }
  }
}
```

### Login
```graphql
mutation {
  tokenAuth(email: "student@example.com", password: "securepassword123") {
    token
    payload
    refreshExpiresIn
  }
}
```

### Get current user
```graphql
query {
  me {
    id
    email
    username
    fullName
    role
  }
}
```

### List courses
```graphql
query {
  courses {
    id
    title
    description
    instructor {
      id
      email
      fullName
    }
    studentCount
    moduleCount
    status
  }
}
```

## Authentication

To authenticate with GraphQL API endpoints, include the JWT token in the HTTP Authorization header:

```
Authorization: JWT <your-token>
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

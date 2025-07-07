# Aperture Booking - Planning & Architecture

## Project Overview
Aperture Booking is a Django-based laboratory resource booking system designed for academic institutions. It provides conflict-free booking management, group collaboration, and comprehensive usage analytics.

## Architecture

### Technology Stack
- **Backend**: Django 4.2+ with Django REST Framework
- **Database**: SQLite (dev), MySQL/PostgreSQL (production)
- **Frontend**: Bootstrap 5, FullCalendar, JavaScript ES6+
- **Task Queue**: Celery with Redis (optional)
- **Web Server**: Gunicorn (production)

### Key Components
1. **booking/** - Main Django app containing:
   - Models for resources, bookings, users, groups
   - Views for calendar, booking management, analytics
   - API endpoints via Django REST Framework
   - Management commands for maintenance and notifications

2. **aperture_booking/** - Django project configuration
   - Settings for development and production
   - URL routing
   - WSGI configuration

3. **static/** - Frontend assets
   - JavaScript modules for calendar functionality
   - CSS for theming and responsive design

4. **templates/** - Django templates
   - Booking system UI templates
   - Registration/authentication templates

## Build Instructions

### Development Environment

1. **Prerequisites**
   ```bash
   # Python 3.8 or higher
   python --version
   
   # pip package manager
   pip --version
   ```

2. **Setup Virtual Environment**
   ```bash
   # Create virtual environment
   python -m venv venv
   
   # Activate virtual environment
   # On Linux/Mac:
   source venv/bin/activate
   # On Windows:
   venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Database Setup**
   ```bash
   # Run migrations
   python manage.py migrate
   
   # Create superuser
   python manage.py createsuperuser
   
   # Create email templates
   python manage.py create_email_templates
   ```

5. **Run Development Server**
   ```bash
   python manage.py runserver
   ```
   Access at: http://127.0.0.1:8000

### Production Environment

1. **Environment Variables**
   Create `.env` file with:
   ```env
   SECRET_KEY=your-secret-key
   DEBUG=False
   ALLOWED_HOSTS=yourdomain.com
   
   # Database config
   DB_ENGINE=mysql
   DB_NAME=aperture_booking
   DB_USER=db_user
   DB_PASSWORD=secure_password
   DB_HOST=localhost
   DB_PORT=3306
   
   # Email config
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_USE_TLS=True
   EMAIL_HOST_USER=your-email@domain.com
   EMAIL_HOST_PASSWORD=app-password
   ```

2. **Static Files**
   ```bash
   python manage.py collectstatic
   ```

3. **Gunicorn Setup**
   ```bash
   pip install gunicorn whitenoise
   gunicorn aperture_booking.wsgi:application
   ```

4. **Nginx Configuration**
   See `deploy/nginx.conf` for production nginx setup

## Testing

### Run Test Suite
```bash
# All tests
python manage.py test

# Specific app tests
python manage.py test booking

# With coverage
coverage run --source='.' manage.py test
coverage report
coverage html
```

### Test Categories
- Unit tests: Models, forms, utilities
- Integration tests: Views, API endpoints
- System tests: Full workflows

## Deployment

### Docker Deployment
```bash
# Build image
docker build -t aperture-booking .

# Run container
docker-compose up -d
```

### Manual Deployment
1. Use deployment scripts in `deploy/` directory
2. Configure systemd services for gunicorn
3. Set up nginx reverse proxy
4. Configure SSL certificates

## Key Features Implementation

### Booking System
- Calendar integration using FullCalendar library
- Conflict detection in `booking/conflicts.py`
- Recurring bookings in `booking/recurring.py`

### Notification System
- Email notifications via Django mail
- In-app notifications stored in database
- SMS framework ready for integration

### Approval Workflows
- Configurable approval rules per resource
- Auto, single-level, tiered, and quota-based approvals
- Approval statistics and analytics

### User Management
- Django authentication system
- Custom UserProfile model for additional fields
- Role-based permissions (Student, Researcher, Lecturer, Lab Manager, Admin)

## Development Workflow

1. **Feature Development**
   - Create feature branch
   - Implement with tests
   - Update documentation
   - Submit pull request

2. **Code Standards**
   - Follow PEP 8
   - Use Black for formatting
   - Write comprehensive docstrings
   - Maintain test coverage above 80%

3. **Database Changes**
   - Create migrations: `python manage.py makemigrations`
   - Review migration files
   - Apply migrations: `python manage.py migrate`

## Maintenance

### Regular Tasks
- Database backups via management commands
- Log rotation configuration
- Performance monitoring
- Security updates

### Monitoring
- Application logs in `logs/` directory
- Database query performance
- Resource utilization metrics
- Error tracking integration ready

## Security Considerations

1. **Authentication**
   - Django's built-in auth system
   - Session security
   - Password policies
   - Optional SSO integration

2. **Authorization**
   - Role-based access control
   - Resource-level permissions
   - API authentication via tokens

3. **Data Protection**
   - CSRF protection enabled
   - XSS prevention
   - SQL injection protection via ORM
   - Input validation on all forms

## Performance Optimization

1. **Database**
   - Indexed fields for common queries
   - Query optimization in views
   - Connection pooling for production

2. **Caching**
   - Redis caching ready
   - Template fragment caching
   - API response caching

3. **Frontend**
   - Static file compression
   - CDN integration ready
   - Lazy loading for large datasets
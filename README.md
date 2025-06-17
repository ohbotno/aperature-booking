# Aperture Booking v1.0.0

An open-source Django application for managing laboratory resource bookings across academic institutions. Prevents double-booking conflicts while enabling group collaboration and providing comprehensive usage analytics.

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Django 4.2+](https://img.shields.io/badge/django-4.2+-green.svg)](https://www.djangoproject.com/)

## 🚀 Features

### Core Functionality
- **Conflict-Free Booking** - Prevents double-booking across all resources
- **Group Collaboration** - Multiple users can share time slots within groups
- **Interactive Calendar** - Click-and-drag booking creation with FullCalendar
- **Flexible Approval Workflows** - Auto, single-level, tiered, and quota-based approvals
- **Rich Analytics** - Usage statistics by user, group, class, and college
- **Maintenance Scheduling** - Integrated maintenance window management

### User Roles
- **Student** - Request bookings, view own/group bookings
- **Researcher** - Create recurring bookings, extended access
- **Lecturer** - Priority booking, class sessions, group management
- **Lab Manager** - Approve bookings, manage resources, view analytics
- **System Administrator** - Full system configuration and user management

### Resource Types
- Robots and automated equipment
- Analytical instruments
- Laboratory rooms and spaces
- Safety cabinets and fume hoods
- Generic bookable equipment

### Interactive Calendar Features
- **Multiple Views** - Month, week, day, and agenda layouts
- **Drag-and-Drop** - Resize and move bookings intuitively
- **Real-time Validation** - Instant conflict detection
- **Resource Filtering** - Show/hide by equipment type
- **Status Indicators** - Color-coded booking states
- **Mobile Responsive** - Touch-friendly interface

## 📋 Requirements

### System Requirements
- Python 3.8 or higher
- Django 4.2 or higher
- Database: MySQL (recommended), PostgreSQL, or SQLite
- Redis (optional, for caching and task queue)

### Browser Support
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## 🛠️ Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/lab-booking-system.git
cd lab-booking-system/aperture_booking
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Database

#### SQLite (Development)
```bash
# Default configuration - no changes needed
python manage.py migrate
```

#### MySQL (Production)
```bash
# Set environment variables
export DB_ENGINE=mysql
export DB_NAME=aperture_booking
export DB_USER=your_username
export DB_PASSWORD=your_password
export DB_HOST=localhost
export DB_PORT=3306

# Create database and run migrations
python manage.py migrate
```

#### PostgreSQL (Production)
```bash
# Set environment variables
export DB_ENGINE=postgresql
export DB_NAME=aperture_booking
export DB_USER=your_username
export DB_PASSWORD=your_password
export DB_HOST=localhost
export DB_PORT=5432

# Create database and run migrations
python manage.py migrate
```

### 5. Create Superuser
```bash
python manage.py createsuperuser
```

### 6. Load Sample Data (Optional)
```bash
python manage.py loaddata fixtures/sample_data.json
```

### 7. Set Up Notification System
```bash
# Create default email templates
python manage.py create_email_templates
```

### 8. Run Development Server
```bash
python manage.py runserver
```

Visit http://127.0.0.1:8000 to access the application.

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Basic Configuration
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Configuration
DB_ENGINE=sqlite  # or mysql, postgresql
DB_NAME=lab_booking
DB_USER=username
DB_PASSWORD=password
DB_HOST=localhost
DB_PORT=3306

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@domain.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@yourdomain.com

# Lab-Specific Settings
LAB_BOOKING_ADVANCE_DAYS=30
TIME_ZONE=America/New_York
```

### Database Setup Scripts

#### MySQL Setup
```sql
CREATE DATABASE lab_booking CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'lab_user'@'localhost' IDENTIFIED BY 'secure_password';
GRANT ALL PRIVILEGES ON lab_booking.* TO 'lab_user'@'localhost';
FLUSH PRIVILEGES;
```

#### PostgreSQL Setup
```sql
CREATE DATABASE lab_booking;
CREATE USER lab_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE lab_booking TO lab_user;
ALTER USER lab_user CREATEDB;
```

## 📊 Approval Workflows

The system supports four types of approval workflows:

### 1. Automatic Approval
- Immediate confirmation for trusted users
- Configurable by resource type and user role
- Ideal for high-trust environments

### 2. Single-Level Approval
- One approver per resource category
- Email notifications to designated approvers
- Suitable for most standard equipment

### 3. Tiered Approval
- Multi-stage approval process
- Escalation for high-value resources
- Department → College → Institution levels

### 4. Quota-Based Approval
- Automatic approval within usage limits
- Manager override for quota exceptions
- Fair access enforcement

### Configuration Example
```python
# In Django admin or management command
ApprovalRule.objects.create(
    name="High-Value Equipment",
    resource=expensive_robot,
    approval_type="tiered",
    user_roles=["student", "researcher"],
    conditions={"min_advance_hours": 24}
)
```

## 📧 Notification System

### Notification Types
The system automatically sends notifications for:
- **Booking Events**: Confirmations, cancellations, reminders
- **Approval Workflow**: Requests and decisions
- **Maintenance Alerts**: Scheduled maintenance affecting bookings
- **Conflicts**: Booking conflicts and resolutions
- **Usage Monitoring**: Quota warnings and limits

### Delivery Methods
- **Email**: HTML and text templates with rich formatting
- **In-App**: Dashboard notifications with read/unread status
- **SMS**: Framework ready for SMS provider integration

### Management Commands
```bash
# Set up email templates (run once during setup)
python manage.py create_email_templates

# Send pending notifications (run via cron job)
python manage.py send_notifications

# Send notifications + booking reminders
python manage.py send_notifications --send-reminders --reminder-hours 24
```

### Production Cron Jobs
```bash
# Send notifications every 10 minutes
*/10 * * * * cd /path/to/project && python manage.py send_notifications

# Send daily reminders at 8 AM
0 8 * * * cd /path/to/project && python manage.py send_notifications --send-reminders
```

### User Preferences
Users can customize their notification preferences through:
- Web interface: `/notifications/preferences/`
- API endpoints for mobile/external applications
- Admin panel for bulk preference management

### Email Configuration
Configure SMTP settings in environment variables:
```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@domain.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
```

## 🏗️ Architecture Overview

### Backend Components
- **Django Framework** - Web application foundation
- **Django REST Framework** - API layer
- **Django ORM** - Database abstraction
- **Celery** - Background task processing
- **Redis** - Caching and message broker

### Frontend Components
- **Bootstrap 5** - Responsive UI framework
- **FullCalendar** - Interactive calendar widget
- **JavaScript ES6+** - Modern client-side functionality
- **Progressive Enhancement** - Accessibility-first design

### Database Schema
```
Users & Profiles → Resources → Bookings → Approval Rules
                           ↓
                    Maintenance Windows
                           ↓
                    Usage Statistics
```

## 🔐 Security Features

### Authentication
- Built-in Django authentication
- Extensible for SSO integration (OAuth, SAML, LDAP)
- Role-based permission system
- Session security

### Data Protection
- CSRF protection
- SQL injection prevention
- XSS mitigation
- Input validation and sanitization

### Audit Trail
- Complete booking history
- User action logging
- Change tracking
- Export capabilities

## 📱 Mobile Support

### Responsive Design
- Touch-friendly interface
- Mobile-optimized booking forms
- Swipe gestures for calendar navigation
- Offline capability (planned)

### Progressive Web App
- App-like experience
- Home screen installation
- Push notifications (planned)
- Background sync (planned)

## 🧪 Testing

### Run Test Suite
```bash
# Run all tests
python manage.py test

# Run with coverage
pip install coverage
coverage run --source='.' manage.py test
coverage report
coverage html
```

### Test Categories
- Model validation tests
- API endpoint tests
- Calendar functionality tests
- Permission and security tests
- Database constraint tests

## 🚀 Deployment

### Production Setup
```bash
# Install production dependencies
pip install gunicorn whitenoise

# Collect static files
python manage.py collectstatic

# Run production server
gunicorn aperture_booking.wsgi:application
```

### Docker Deployment
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN python manage.py collectstatic --noinput

EXPOSE 8000
CMD ["gunicorn", "lab_booking.wsgi:application"]
```

### Environment-Specific Settings
- Development: SQLite, Debug mode, Console email
- Staging: PostgreSQL, Limited debug, SMTP email
- Production: MySQL/PostgreSQL, No debug, Full monitoring

## 📈 Usage Statistics

### Available Metrics
- **Resource Utilization** - Usage percentage by equipment
- **User Activity** - Bookings per user/group/department
- **Peak Usage Analysis** - Demand patterns by time
- **Booking Success Rate** - Approval/rejection ratios
- **Maintenance Impact** - Downtime analysis

### Dashboard Features
- Real-time statistics
- Customizable date ranges
- Export functionality (CSV, PDF)
- Graphical visualizations
- Automated reports

## 🔧 Customization

### Extending Models
```python
# booking/models.py
class CustomResource(Resource):
    specialized_field = models.CharField(max_length=100)
    
    class Meta:
        proxy = True
```

### Custom Approval Logic
```python
# booking/approvals.py
def custom_approval_logic(booking, user):
    if booking.resource.cost > 10000:
        return 'tiered'
    return 'auto'
```

### Theme Customization
```css
/* static/css/custom.css */
:root {
    --primary-color: #your-brand-color;
    --secondary-color: #your-accent-color;
}
```

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create feature branch: `git checkout -b feature/new-feature`
3. Make changes and add tests
4. Run test suite: `python manage.py test`
5. Submit pull request

### Code Standards
- Follow PEP 8 for Python code
- Use Black for code formatting
- Write comprehensive tests
- Update documentation

### Reporting Issues
- Use GitHub Issues for bug reports
- Include system information and steps to reproduce
- Attach relevant log files
- Specify expected vs. actual behavior

## 📄 License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

### GPL-3.0 Summary
- ✅ Commercial use allowed
- ✅ Modification allowed
- ✅ Distribution allowed
- ✅ Patent use allowed
- ❗ License and copyright notice required
- ❗ Source code must be disclosed
- ❗ Same license required for derivatives

## 🆘 Support

### Documentation
- [Full Requirements](PROJECT.md) - Complete specification
- [Development Tasks](TODO.md) - Roadmap and tasks
- [API Documentation](docs/api.md) - REST API reference

### Community
- GitHub Issues - Bug reports and feature requests
- Discussions - General questions and ideas
- Wiki - Community documentation

### Professional Support
For institutional deployment, training, or custom development:
- Email: support@lab-booking-system.org
- Website: https://lab-booking-system.org

---

**Aperture Booking v1.0.0** - A Lab booking system. Streamlining laboratory resource management for academic institutions worldwide.

Made with ❤️ for the open source community.
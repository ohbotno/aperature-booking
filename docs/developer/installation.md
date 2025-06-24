# Installation and Deployment Guide

Complete guide for installing, configuring, and deploying Aperture Booking in development, staging, and production environments.

## System Requirements

### Minimum Requirements
```
Operating System:
- Ubuntu 20.04 LTS or later
- CentOS 8 or later
- Windows Server 2019 or later
- macOS 11 or later (development only)

Hardware:
- CPU: 2 cores, 2.0 GHz minimum
- RAM: 4 GB minimum, 8 GB recommended
- Storage: 20 GB minimum, SSD recommended
- Network: Broadband internet connection

Software Dependencies:
- Python 3.9 or later
- PostgreSQL 12+ or MySQL 8.0+
- Redis 6.0+ (for caching and sessions)
- Node.js 16+ (for asset compilation)
```

### Recommended Production Specifications
```
Hardware:
- CPU: 4+ cores, 3.0 GHz
- RAM: 16 GB or more
- Storage: 100 GB+ SSD with backup
- Network: Dedicated high-speed connection

Infrastructure:
- Load balancer (nginx, Apache, or cloud LB)
- Database server (separate from application)
- Redis cluster for high availability
- File storage (local or cloud storage)
- SSL certificate (Let's Encrypt or commercial)
```

## Development Installation

### Local Development Setup

#### 1. Install System Dependencies

##### Ubuntu/Debian
```bash
# Update package list
sudo apt update

# Install Python and development tools
sudo apt install python3.9 python3.9-dev python3-pip python3-venv

# Install PostgreSQL
sudo apt install postgresql postgresql-contrib libpq-dev

# Install Redis
sudo apt install redis-server

# Install Node.js (via NodeSource)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs

# Install additional dependencies
sudo apt install git curl wget build-essential
```

##### macOS (using Homebrew)
```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install python@3.9 postgresql redis node git

# Start services
brew services start postgresql
brew services start redis
```

##### Windows (using Chocolatey)
```powershell
# Install Chocolatey (run as Administrator)
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Install dependencies
choco install python3 postgresql redis nodejs git
```

#### 2. Clone Repository and Setup Environment

```bash
# Clone the repository
git clone https://github.com/ohbotno/aperture-booking.git
cd aperture-booking

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# Linux/macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip

# Install Python dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt
```

#### 3. Database Setup

##### PostgreSQL Setup
```bash
# Start PostgreSQL service (if not already running)
sudo systemctl start postgresql  # Linux
brew services start postgresql   # macOS

# Create database user
sudo -u postgres createuser --interactive --pwprompt aperture_user

# Create database
sudo -u postgres createdb aperture_booking --owner aperture_user

# Verify connection
psql -h localhost -U aperture_user -d aperture_booking -c "SELECT version();"
```

##### MySQL Setup (Alternative)
```bash
# Start MySQL service
sudo systemctl start mysql  # Linux
brew services start mysql   # macOS

# Create database and user
mysql -u root -p << EOF
CREATE DATABASE aperture_booking CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'aperture_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON aperture_booking.* TO 'aperture_user'@'localhost';
FLUSH PRIVILEGES;
EOF
```

#### 4. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit configuration file
nano .env  # or your preferred editor
```

##### Development Environment File (.env)
```bash
# Database Configuration
DATABASE_URL=postgresql://aperture_user:password@localhost:5432/aperture_booking
# Alternative MySQL:
# DATABASE_URL=mysql://aperture_user:password@localhost:3306/aperture_booking

# Django Settings
SECRET_KEY=your-secret-key-here-generate-new-one
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Email Configuration (for development)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-app-password

# Static Files
STATIC_URL=/static/
STATIC_ROOT=/path/to/static/files/
MEDIA_URL=/media/
MEDIA_ROOT=/path/to/media/files/

# Security (development only)
SECURE_SSL_REDIRECT=False
SECURE_HSTS_SECONDS=0
```

#### 5. Initialize Application

```bash
# Run database migrations
python manage.py migrate

# Create superuser account
python manage.py createsuperuser

# Install Node.js dependencies
npm install

# Build static assets
npm run build

# Collect static files
python manage.py collectstatic --noinput

# Load sample data (optional)
python manage.py loaddata sample_data.json
```

#### 6. Start Development Server

```bash
# Start Django development server
python manage.py runserver

# In another terminal, start asset watcher (optional)
npm run watch

# Access the application
# http://localhost:8000 - Main application
# http://localhost:8000/admin - Django admin interface
```

## Production Deployment

Aperture Booking provides multiple production deployment options:

1. **Automated Source Deployment** - Automated script handles complete setup
2. **Docker Deployment** - Containerized production environment 
3. **Manual Source Deployment** - Step-by-step manual installation

Choose the method that best fits your infrastructure needs.

### Automated Source Deployment (Recommended)

The easiest way to deploy Aperture Booking in production:

```bash
# Download and run the automated installer
curl -fsSL https://raw.githubusercontent.com/ohbotno/aperture-booking/main/deploy/install.sh | sudo bash

# Follow the interactive prompts to configure:
# - Domain name
# - Database credentials
# - SSL certificate setup
# - Email configuration
```

The installer automatically handles:
- System dependency installation
- PostgreSQL and Redis setup
- Application deployment and configuration
- Nginx reverse proxy with SSL
- SystemD service creation
- Security hardening
- Automated backup configuration

### Manual Source Deployment

For custom installations or when you need full control over the process.

#### 1. Server Setup (Ubuntu 20.04 LTS)

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3.9 python3.9-dev python3-pip python3-venv \
    postgresql postgresql-contrib libpq-dev redis-server \
    nginx supervisor git curl wget build-essential \
    certbot python3-certbot-nginx

# Create application user
sudo adduser --system --group aperture --home /opt/aperture

# Create application directory
sudo mkdir -p /opt/aperture/booking
sudo chown aperture:aperture /opt/aperture/booking
```

#### 2. Database Configuration

```bash
# Configure PostgreSQL
sudo -u postgres psql << EOF
CREATE DATABASE aperture_booking;
CREATE USER aperture_user WITH PASSWORD 'secure_password_here';
ALTER ROLE aperture_user SET client_encoding TO 'utf8';
ALTER ROLE aperture_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE aperture_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE aperture_booking TO aperture_user;
EOF

# Configure PostgreSQL settings
sudo nano /etc/postgresql/12/main/postgresql.conf

# Add/modify these settings:
# shared_preload_libraries = 'pg_stat_statements'
# max_connections = 100
# shared_buffers = 256MB
# effective_cache_size = 1GB

# Configure authentication
sudo nano /etc/postgresql/12/main/pg_hba.conf

# Add line for application user:
# local   aperture_booking    aperture_user                     md5

# Restart PostgreSQL
sudo systemctl restart postgresql
```

#### 3. Source-Based Application Deployment

Aperture Booking includes automated production deployment scripts.

##### Option A: Automated Installation (Recommended)

```bash
# Download and run the installation script
curl -fsSL https://raw.githubusercontent.com/ohbotno/aperture-booking/main/deploy/install.sh | sudo bash

# Or download and review first:
wget https://raw.githubusercontent.com/ohbotno/aperture-booking/main/deploy/install.sh
chmod +x install.sh
sudo ./install.sh
```

The automated installer will:
- Install all system dependencies
- Configure PostgreSQL and Redis
- Set up the application environment
- Configure Nginx and SSL
- Create systemd services
- Set up automated backups

##### Option B: Manual Installation

```bash
# Switch to application user
sudo -u aperture -i

# Clone repository
cd /opt/aperture
git clone https://github.com/ohbotno/aperture-booking.git booking
cd booking

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn psycopg2-binary

# Install Node.js dependencies
npm install --production

# Build assets
npm run build:prod
```

#### 4. Production Environment Configuration

```bash
# Create production environment file
sudo -u aperture nano /opt/aperture/booking/.env
```

##### Production Environment File
```bash
# Database Configuration
DATABASE_URL=postgresql://aperture_user:secure_password@localhost:5432/aperture_booking

# Django Settings
SECRET_KEY=generate-secure-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.your-provider.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=noreply@your-domain.com
EMAIL_HOST_PASSWORD=your-email-password

# Static and Media Files
STATIC_URL=/static/
STATIC_ROOT=/opt/aperture/booking/static/
MEDIA_URL=/media/
MEDIA_ROOT=/opt/aperture/booking/media/

# Security Settings
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
SECURE_CONTENT_TYPE_NOSNIFF=True
SECURE_BROWSER_XSS_FILTER=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/aperture/booking.log
```

#### 5. Initialize Production Application

```bash
# Run as aperture user
sudo -u aperture -i
cd /opt/aperture/booking
source venv/bin/activate

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput

# Test configuration
python manage.py check --deploy
```

### Web Server Configuration

Aperture Booking includes pre-configured production files for easy deployment.

#### SystemD Services (Recommended)

The application includes optimized SystemD service files:

```bash
# Copy service files (included in deploy/ directory)
sudo cp deploy/aperture-booking.service /etc/systemd/system/
sudo cp deploy/aperture-booking.socket /etc/systemd/system/
sudo cp deploy/aperture-booking-scheduler.service /etc/systemd/system/

# Enable and start services
sudo systemctl daemon-reload
sudo systemctl enable aperture-booking.socket
sudo systemctl enable aperture-booking-scheduler.service
sudo systemctl start aperture-booking.socket
sudo systemctl start aperture-booking-scheduler.service

# Check service status
sudo systemctl status aperture-booking.socket
sudo systemctl status aperture-booking-scheduler.service
```

#### Nginx Configuration

Multiple Nginx configurations are provided for different deployment scenarios:

##### Production with HTTPS (Recommended)
```bash
# Copy and enable the production configuration
sudo cp deploy/nginx.conf /etc/nginx/sites-available/aperture-booking
sudo ln -s /etc/nginx/sites-available/aperture-booking /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Edit configuration for your domain
sudo nano /etc/nginx/sites-available/aperture-booking
# Update server_name to your domain

# Test and restart
sudo nginx -t
sudo systemctl restart nginx
```

##### HTTP-Only Development/Testing
```bash
# For development or internal testing
sudo cp deploy/nginx-http-only.conf /etc/nginx/sites-available/aperture-booking
sudo ln -s /etc/nginx/sites-available/aperture-booking /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### SSL Certificate Setup

The included SSL setup script automates certificate installation:

```bash
# Run SSL setup script
sudo bash deploy/setup_ssl.sh your-domain.com

# Or manually with Certbot:
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Automatic renewal is configured by default
sudo systemctl status certbot.timer
```

#### Alternative: Supervisor Configuration

If you prefer Supervisor over SystemD:

```bash
# Copy supervisor configuration
sudo cp deploy/supervisor.conf /etc/supervisor/conf.d/aperture-booking.conf

# Update supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start aperture-booking
```

### Database Optimization

#### PostgreSQL Performance Tuning

```bash
# Edit PostgreSQL configuration
sudo nano /etc/postgresql/12/main/postgresql.conf
```

```sql
# Memory settings
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9

# WAL settings
wal_buffers = 16MB
checkpoint_segments = 32

# Connection settings
max_connections = 100

# Query planner
random_page_cost = 1.1
effective_io_concurrency = 200

# Logging
log_destination = 'csvlog'
logging_collector = on
log_directory = 'pg_log'
log_filename = 'postgresql-%Y-%m-%d_%H%M%S.log'
log_min_duration_statement = 1000
```

```bash
# Restart PostgreSQL
sudo systemctl restart postgresql
```

#### Database Backup Configuration

```bash
# Create backup script
sudo nano /opt/aperture/backup-db.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/opt/aperture/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="aperture_booking"
DB_USER="aperture_user"

# Create backup directory if it doesn't exist
mkdir -p $BACKUP_DIR

# Create database backup
pg_dump -h localhost -U $DB_USER -W $DB_NAME | gzip > $BACKUP_DIR/aperture_booking_$DATE.sql.gz

# Keep only last 30 days of backups
find $BACKUP_DIR -name "aperture_booking_*.sql.gz" -mtime +30 -delete

echo "Backup completed: aperture_booking_$DATE.sql.gz"
```

```bash
# Make script executable
sudo chmod +x /opt/aperture/backup-db.sh

# Add to crontab for automated backups
sudo crontab -e

# Add daily backup at 2 AM:
0 2 * * * /opt/aperture/backup-db.sh
```

## Docker Deployment

Aperture Booking includes comprehensive Docker support for both development and production environments.

### Quick Start with Docker

```bash
# Clone the repository
git clone https://github.com/ohbotno/aperture-booking.git
cd aperture-booking

# Copy environment template
cp .env.example .env

# Edit environment variables (especially DB_PASSWORD and SECRET_KEY)
nano .env

# Start the application stack
docker-compose up -d

# Run initial setup
docker-compose exec app python manage.py migrate
docker-compose exec app python manage.py createsuperuser

# Access the application at http://localhost
```

### Production Docker Configuration

The included Docker configuration provides a complete production-ready stack:

#### Included Services
- **Application**: Django app with Gunicorn + Nginx
- **Database**: PostgreSQL 15 with automated backups
- **Cache**: Redis 7 for sessions and caching
- **Backup**: Optional automated database backup service

#### Key Features
- **Multi-stage build** for optimized image size
- **Health checks** for all services with proper dependency management
- **Volume management** for persistent data (database, static files, media, logs, backups)
- **Security hardening** with non-root users and security headers
- **Environment-based configuration** for easy deployment customization
- **Automated initialization** with database setup and static file collection

### Environment Configuration

Create and configure your `.env` file with production values:

```bash
# Database settings
DB_NAME=aperture_booking
DB_USER=aperture_booking
DB_PASSWORD=your-secure-database-password

# Django settings
SECRET_KEY=your-secret-key-here-generate-new-one
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com

# HTTPS settings (set to True for production)
USE_HTTPS=True

# Email configuration
EMAIL_HOST=smtp.your-provider.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=noreply@your-domain.com
EMAIL_HOST_PASSWORD=your-email-password
DEFAULT_FROM_EMAIL=noreply@your-domain.com

# Admin settings
ADMIN_EMAIL=admin@your-domain.com

# Port configuration (optional)
HTTP_PORT=80
HTTPS_PORT=443
```

### Deployment Commands

```bash
# Production deployment
docker-compose up -d --build

# Run database migrations
docker-compose exec app python manage.py migrate

# Create admin user
docker-compose exec app python manage.py createsuperuser

# Check application health
docker-compose exec app curl -f http://localhost/health/

# View application logs
docker-compose logs -f app

# View all service logs
docker-compose logs -f

# Update application (pull latest changes)
git pull origin main
docker-compose up -d --build

# Stop services
docker-compose down

# Stop and remove all data (WARNING: destructive)
docker-compose down -v
```

### SSL/HTTPS Configuration

For production HTTPS deployment:

1. **Domain Setup**: Point your domain to the server running Docker
2. **Environment Variables**: Set `USE_HTTPS=True` and configure your domain in `ALLOWED_HOSTS`
3. **SSL Certificates**: The Nginx configuration supports SSL certificates mounted at `/etc/nginx/ssl/`

```bash
# Example SSL certificate setup
# Place your certificates in ./ssl/ directory
mkdir -p ssl
# Copy your SSL certificate files:
# ssl/cert.pem (certificate)
# ssl/key.pem (private key)

# Update docker-compose.yml to mount SSL certificates
# The ssl directory will be mounted to /etc/nginx/ssl/ in the container
```

### Backup Service

Enable automated database backups:

```bash
# Start backup service (runs daily backups)
docker-compose --profile backup up -d backup

# Manual backup
docker-compose run --rm backup

# View backup files
ls -la backups/db/
```

### Monitoring and Maintenance

```bash
# Check service health
docker-compose ps

# View resource usage
docker stats

# Check disk usage
docker system df

# Clean up unused resources
docker system prune

# Update to latest images
docker-compose pull
docker-compose up -d
```

### Development with Docker

For development environments, use the same setup but with development-specific environment variables:

```bash
# Development environment
DEBUG=True
USE_HTTPS=False
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

### Scaling and Load Balancing

The Docker configuration supports horizontal scaling:

```bash
# Scale application containers
docker-compose up -d --scale app=3

# Use external load balancer to distribute traffic
# The application containers will be available on different ports
```

## Monitoring and Maintenance

### Application Monitoring

#### 1. Health Check Endpoint

```python
# Add to urls.py
from django.http import JsonResponse
from django.views.decorators.cache import never_cache

@never_cache
def health_check(request):
    return JsonResponse({
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'version': '1.1.0'
    })
```

#### 2. Log Configuration

```python
# Add to settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/aperture/booking.log',
            'maxBytes': 1024*1024*10,  # 10 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['file'],
        'level': 'INFO',
    },
}
```

#### 3. Performance Monitoring

```bash
# Install monitoring tools
pip install django-debug-toolbar
pip install django-silk

# Add to requirements.txt
echo "django-debug-toolbar==3.2.4" >> requirements.txt
echo "django-silk==5.0.1" >> requirements.txt
```

### Backup and Recovery

Aperture Booking includes comprehensive backup automation through the web interface and command-line tools.

#### Automated Backup System

The application includes a built-in backup management system accessible via the Site Administrator dashboard:

- **Scheduled Backups**: Configure automatic daily/weekly/monthly backups
- **Manual Backups**: Create on-demand backups through the web interface
- **Backup Monitoring**: View backup history and status
- **Automated Cleanup**: Configurable retention policies

#### Manual Backup Commands

```bash
# Create manual backup using Django command
python manage.py create_backup

# Run scheduled backups
python manage.py run_scheduled_backups

# Restore from backup
python manage.py restore_backup /path/to/backup.tar.gz
```

#### Legacy Backup Script (Alternative)

```bash
#!/bin/bash
# /opt/aperture/backup-full.sh

BACKUP_DIR="/opt/aperture/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Database backup
pg_dump -h localhost -U aperture_user aperture_booking | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Media files backup
tar -czf $BACKUP_DIR/media_$DATE.tar.gz /opt/aperture/booking/media/

# Application backup (excluding virtual environment)
tar -czf $BACKUP_DIR/app_$DATE.tar.gz --exclude='venv' --exclude='node_modules' /opt/aperture/booking/

# Clean old backups (keep 30 days)
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete

echo "Full backup completed: $DATE"
```

### Security Hardening

#### 1. Firewall Configuration

```bash
# Configure UFW firewall
sudo ufw enable
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw status
```

#### 2. Security Updates

```bash
# Automatic security updates
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades

# Configure automatic updates
sudo nano /etc/apt/apt.conf.d/50unattended-upgrades
```

#### 3. Application Security

```python
# Add to settings.py for production
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_TZ = True
TIME_ZONE = 'UTC'

# Session security
SESSION_COOKIE_AGE = 3600  # 1 hour
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_HTTPONLY = True

# CSRF protection
CSRF_COOKIE_HTTPONLY = True
CSRF_USE_SESSIONS = True
```

## Troubleshooting

### Common Installation Issues

#### Database Connection Problems

```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check connection
psql -h localhost -U aperture_user -d aperture_booking -c "SELECT 1;"

# View PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-12-main.log
```

#### Permission Issues

```bash
# Fix file permissions
sudo chown -R aperture:aperture /opt/aperture/booking
sudo chmod -R 755 /opt/aperture/booking

# Fix media directory permissions
sudo chown -R aperture:www-data /opt/aperture/booking/media
sudo chmod -R 775 /opt/aperture/booking/media
```

#### Static Files Not Loading

```bash
# Collect static files
python manage.py collectstatic --clear --noinput

# Check nginx configuration
sudo nginx -t

# Verify file permissions
ls -la /opt/aperture/booking/static/
```

### Performance Issues

#### Database Performance

```sql
-- Check slow queries
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;

-- Check database size
SELECT pg_size_pretty(pg_database_size('aperture_booking'));
```

#### Application Performance

```bash
# Check memory usage
ps aux | grep gunicorn
free -m

# Check disk usage
df -h
du -sh /opt/aperture/booking/*

# Monitor logs
tail -f /var/log/aperture/booking.log
```

## Update System

Aperture Booking includes a built-in update system that integrates with GitHub releases.

### Automatic Update Checking

The system automatically checks for updates from the `ohbotno/aperture-booking` repository:

- **Dashboard Integration**: View current and available versions in the Site Administrator dashboard
- **Update Notifications**: Automatic notification of available updates
- **Release Notes**: View changelog and release information before updating
- **Background Checks**: Automatic checking for updates every 24 hours

### Update Management

Access update management through the Site Administrator interface:

1. **Navigate to Site Administration** → **Updates** section
2. **View Current Version**: See currently installed version and update status
3. **Check for Updates**: Manual update checking with real-time status
4. **Update Installation**: One-click update process with backup integration
5. **Update History**: View previous updates and their status

### Manual Update Process

For command-line updates or automated deployments:

```bash
# Check for available updates
python manage.py check_updates

# View update status and information
python manage.py update_status

# For Docker deployments:
git pull origin main
docker-compose up -d --build

# For source deployments:
bash deploy/update.sh
```

### Update Configuration

Configure update behavior in the Site Administrator dashboard:

- **Update Source**: GitHub repository (default: ohbotno/aperture-booking)
- **Update Channel**: Release branch or pre-release versions
- **Backup Integration**: Automatic backup before updates
- **Notification Settings**: Email notifications for available updates

---

**Successfully deploying Aperture Booking requires careful attention to security, performance, and reliability.** The included deployment tools and automation features help ensure a robust, scalable installation that meets your institution's needs.

*For ongoing maintenance, backup management, and system updates, see the [Administration Guide](../admin/) and [Site Administrator Dashboard](../admin/system-setup.md#site-administrator-dashboard) documentation.*
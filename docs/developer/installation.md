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
git clone https://github.com/your-org/aperture-booking.git
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

### Server Preparation

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

#### 3. Application Deployment

```bash
# Switch to application user
sudo -u aperture -i

# Clone repository
cd /opt/aperture
git clone https://github.com/your-org/aperture-booking.git booking
cd booking

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn

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

#### 1. Gunicorn Configuration

```bash
# Create Gunicorn configuration
sudo -u aperture nano /opt/aperture/booking/gunicorn.conf.py
```

```python
# Gunicorn configuration file
bind = "127.0.0.1:8000"
workers = 4
worker_class = "gevent"
worker_connections = 1000
max_requests = 5000
max_requests_jitter = 500
preload_app = True
timeout = 120
keepalive = 5

# Logging
accesslog = "/var/log/aperture/gunicorn-access.log"
errorlog = "/var/log/aperture/gunicorn-error.log"
loglevel = "info"

# Process naming
proc_name = "aperture-booking"

# User and group
user = "aperture"
group = "aperture"

# Security
limit_request_line = 8190
limit_request_fields = 200
limit_request_field_size = 8190
```

#### 2. Supervisor Configuration

```bash
# Create supervisor configuration
sudo nano /etc/supervisor/conf.d/aperture-booking.conf
```

```ini
[program:aperture-booking]
command=/opt/aperture/booking/venv/bin/gunicorn aperture_booking.wsgi:application -c /opt/aperture/booking/gunicorn.conf.py
directory=/opt/aperture/booking
user=aperture
group=aperture
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/aperture/supervisor.log
environment=PATH="/opt/aperture/booking/venv/bin"
```

```bash
# Create log directory
sudo mkdir -p /var/log/aperture
sudo chown aperture:aperture /var/log/aperture

# Update supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start aperture-booking
```

#### 3. Nginx Configuration

```bash
# Create nginx site configuration
sudo nano /etc/nginx/sites-available/aperture-booking
```

```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # Security headers
    add_header Strict-Transport-Security "max-age=63072000" always;
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";

    # Main application
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }

    # Static files
    location /static/ {
        alias /opt/aperture/booking/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Media files
    location /media/ {
        alias /opt/aperture/booking/media/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Security.txt
    location /.well-known/security.txt {
        return 301 https://your-domain.com/security.txt;
    }
}
```

```bash
# Enable site and restart nginx
sudo ln -s /etc/nginx/sites-available/aperture-booking /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### 4. SSL Certificate Setup

```bash
# Obtain SSL certificate using Let's Encrypt
sudo certbot certonly --nginx -d your-domain.com -d www.your-domain.com

# Set up automatic renewal
sudo crontab -e

# Add this line:
0 12 * * * /usr/bin/certbot renew --quiet
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

### Docker Configuration

#### 1. Dockerfile

```dockerfile
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
        libpq-dev \
        gcc \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Install Node.js dependencies and build assets
COPY package*.json /app/
RUN npm ci --only=production

# Copy project
COPY . /app/

# Build static assets
RUN npm run build:prod

# Collect static files
RUN python manage.py collectstatic --noinput

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Start application
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "aperture_booking.wsgi:application"]
```

#### 2. Docker Compose Configuration

```yaml
# docker-compose.yml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://aperture:password@db:5432/aperture_booking
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    volumes:
      - static_volume:/app/static
      - media_volume:/app/media

  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=aperture_booking
      - POSTGRES_USER=aperture
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:6-alpine
    ports:
      - "6379:6379"

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - static_volume:/app/static
      - media_volume:/app/media
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - web

volumes:
  postgres_data:
  static_volume:
  media_volume:
```

#### 3. Docker Deployment Commands

```bash
# Build and start services
docker-compose up -d --build

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# View logs
docker-compose logs -f web

# Stop services
docker-compose down
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

#### Automated Backup Script

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

---

**Successfully deploying Aperture Booking requires careful attention to security, performance, and reliability.** Follow these guidelines to ensure a robust, scalable installation that meets your institution's needs.

*For ongoing maintenance and updates, see the [Administration Guide](../admin/) and [Troubleshooting](../troubleshooting/) sections.*
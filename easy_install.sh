#!/bin/bash
#
# Aperture Booking - One-Command Production Installation
# 
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/ohbotno/aperture-booking/main/easy_install.sh | sudo bash
# OR
#   wget -qO- https://raw.githubusercontent.com/ohbotno/aperture-booking/main/easy_install.sh | sudo bash
#
# This script automatically installs Aperture Booking with:
# - Nginx + Gunicorn
# - PostgreSQL database
# - Database caching
# - SSL certificate (optional)
# - Systemd services
# - Automatic backups
#

set -e

# Configuration
REPO_URL="https://github.com/ohbotno/aperture-booking.git"
BRANCH="main"
APP_NAME="aperture-booking"
APP_USER="aperture"
DB_NAME="aperture_booking"
DB_USER="aperture_booking"
APP_DIR="/opt/aperture-booking"
DOMAIN=""
EMAIL=""
DB_PASSWORD=$(openssl rand -base64 32)
SECRET_KEY=$(openssl rand -base64 50)

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# ASCII Art Banner
show_banner() {
    echo -e "${BLUE}"
    cat << "EOF"
                          _                  
    /\                   | |                 
   /  \   _ __   ___ _ __| |_ _   _ _ __ ___ 
  / /\ \ | '_ \ / _ \ '__| __| | | | '__/ _ \
 / ____ \| |_) |  __/ |  | |_| |_| | | |  __/
/_/__  \_\ .__/ \___|_| _ \__|\__,_|_|  \___|
|  _ \   | |      | |  (_)                   
| |_) | _|_|  ___ | | ___ _ __   __ _        
|  _ < / _ \ / _ \| |/ / | '_ \ / _` |       
| |_) | (_) | (_) |   <| | | | | (_| |       
|____/ \___/ \___/|_|\_\_|_| |_|\__, |       
                                 __/ |       
                                |___/        
EOF
    echo -e "${NC}"
    echo -e "${GREEN}One-Command Production Installation${NC}"
    echo
}

# Logging functions
log() { echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"; }
success() { echo -e "${GREEN}[✓]${NC} $1"; }
warning() { echo -e "${YELLOW}[!]${NC} $1"; }
error() { echo -e "${RED}[✗]${NC} $1"; exit 1; }

# Check root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "This script must be run as root (use sudo)"
    fi
}

# Get user input
get_configuration() {
    echo -e "${YELLOW}Configuration Setup${NC}"
    echo "==================="
    
    # Check if running interactively
    if [ -t 0 ]; then
        # Interactive mode - get user input
        read -p "Enter your domain name (e.g., booking.university.edu): " DOMAIN
        if [[ -z "$DOMAIN" ]]; then
            DOMAIN="localhost"
            warning "No domain provided, using localhost"
        fi
        
        # Admin email
        read -p "Enter admin email address: " EMAIL
        if [[ -z "$EMAIL" ]]; then
            EMAIL="admin@$DOMAIN"
            warning "No email provided, using $EMAIL"
        fi
        
        # SSL Certificate
        if [[ "$DOMAIN" != "localhost" ]]; then
            read -p "Install SSL certificate? (y/n): " -n 1 -r
            echo
            INSTALL_SSL=$REPLY
        else
            INSTALL_SSL="n"
        fi
    else
        # Non-interactive mode - use defaults or environment variables
        DOMAIN="${APERTURE_DOMAIN:-localhost}"
        EMAIL="${APERTURE_EMAIL:-admin@$DOMAIN}"
        INSTALL_SSL="${APERTURE_SSL:-n}"
        
        warning "Running in non-interactive mode. Using defaults:"
        warning "  Domain: $DOMAIN"
        warning "  Email: $EMAIL"
        warning "  SSL: $([ "$INSTALL_SSL" == "y" ] && echo "Yes" || echo "No")"
        warning ""
        warning "To customize, set environment variables:"
        warning "  APERTURE_DOMAIN=yourdomain.com"
        warning "  APERTURE_EMAIL=admin@yourdomain.com"
        warning "  APERTURE_SSL=y"
        warning ""
        warning "Or download and run the script directly:"
        warning "  wget https://raw.githubusercontent.com/ohbotno/aperture-booking/main/easy_install.sh"
        warning "  chmod +x easy_install.sh"
        warning "  sudo ./easy_install.sh"
        echo
        sleep 5
    fi
    
    echo
    log "Configuration summary:"
    log "  Domain: $DOMAIN"
    log "  Email: $EMAIL"
    log "  SSL: $([ "$INSTALL_SSL" == "y" ] && echo "Yes" || echo "No")"
    echo
    
    if [ -t 0 ]; then
        read -p "Continue with installation? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 0
        fi
    else
        log "Starting installation in 5 seconds... (Ctrl+C to cancel)"
        sleep 5
    fi
}

# Detect OS
detect_os() {
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        OS=$ID
        VER=$VERSION_ID
    else
        error "Cannot detect OS"
    fi
    
    case $OS in
        ubuntu|debian)
            PKG_MANAGER="apt-get"
            ;;
        centos|rhel|fedora)
            PKG_MANAGER="yum"
            ;;
        *)
            error "Unsupported OS: $OS"
            ;;
    esac
    
    success "Detected $OS $VER"
}

# Install dependencies
install_dependencies() {
    log "Installing system dependencies..."
    
    if [[ "$PKG_MANAGER" == "apt-get" ]]; then
        apt-get update -qq
        DEBIAN_FRONTEND=noninteractive apt-get install -y -qq \
            python3 python3-pip python3-venv python3-dev \
            postgresql postgresql-contrib \
            nginx \
            build-essential libpq-dev \
            pkg-config \
            default-libmysqlclient-dev \
            libssl-dev \
            git curl wget unzip \
            certbot python3-certbot-nginx \
            supervisor
    elif [[ "$PKG_MANAGER" == "yum" ]]; then
        yum install -y epel-release
        yum install -y \
            python3 python3-pip python3-devel \
            postgresql postgresql-server postgresql-contrib \
            nginx \
            gcc postgresql-devel \
            pkgconfig \
            mysql-devel \
            openssl-devel \
            git curl wget unzip \
            certbot python3-certbot-nginx \
            supervisor
        
        # Initialize PostgreSQL on RHEL/CentOS
        postgresql-setup initdb
    fi
    
    # Verify critical dependencies
    log "Verifying dependencies..."
    if ! command -v pkg-config &> /dev/null; then
        error "pkg-config installation failed. Please install manually: sudo apt-get install pkg-config"
    fi
    
    success "Dependencies installed"
}

# Quick setup
quick_setup() {
    log "Creating application user..."
    useradd --system --home "$APP_DIR" --shell /bin/bash "$APP_USER" 2>/dev/null || true
    
    log "Setting up directories..."
    mkdir -p "$APP_DIR"/{logs,media,static,backups}
    mkdir -p /var/{run,log}/$APP_NAME
    
    # Ensure directories have correct permissions and ownership
    chown "$APP_USER:$APP_USER" /var/run/$APP_NAME /var/log/$APP_NAME
    chmod 755 /var/run/$APP_NAME /var/log/$APP_NAME
    
    log "Cloning repository..."
    if [[ -d "$APP_DIR/.git" ]]; then
        log "Repository already exists, updating..."
        cd "$APP_DIR" && git fetch origin && git reset --hard origin/"$BRANCH" && git pull origin "$BRANCH"
    elif [[ -d "$APP_DIR" ]]; then
        warning "Directory exists but is not a git repository. Backing up and cloning fresh..."
        mv "$APP_DIR" "$APP_DIR.backup.$(date +%Y%m%d_%H%M%S)"
        git clone -b "$BRANCH" "$REPO_URL" "$APP_DIR"
    else
        git clone -b "$BRANCH" "$REPO_URL" "$APP_DIR"
    fi
    
    chown -R "$APP_USER:$APP_USER" "$APP_DIR" /var/{run,log}/$APP_NAME
    
    success "Directory setup complete"
}

# Database setup
setup_database() {
    log "Setting up PostgreSQL database..."
    
    systemctl start postgresql
    systemctl enable postgresql
    
    # Create user and database, handling existing resources gracefully
    sudo -u postgres psql << EOF
-- Drop existing database and user if they exist (for clean reinstalls)
DROP DATABASE IF EXISTS $DB_NAME;
DROP USER IF EXISTS $DB_USER;

-- Create user with password
CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';

-- Create database with proper encoding (using template0 for custom collation)
CREATE DATABASE $DB_NAME 
    OWNER $DB_USER 
    ENCODING 'UTF8' 
    TEMPLATE template0;

-- Grant all privileges
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;

EOF

    # Grant schema privileges in a separate command after database is created
    sudo -u postgres psql -d "$DB_NAME" << EOF
GRANT ALL ON SCHEMA public TO $DB_USER;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO $DB_USER;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO $DB_USER;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO $DB_USER;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO $DB_USER;
EOF
    
    # Test database connection
    log "Testing database connection..."
    if sudo -u postgres psql -d "$DB_NAME" -c "SELECT version();" > /dev/null 2>&1; then
        success "Database configured and connection tested"
    else
        error "Database connection test failed"
    fi
}

# Python setup
setup_python() {
    log "Setting up Python environment..."
    
    cd "$APP_DIR"
    sudo -u "$APP_USER" python3 -m venv venv
    sudo -u "$APP_USER" ./venv/bin/pip install --upgrade pip wheel setuptools
    
    # Try to install mysqlclient with proper flags if needed
    log "Installing Python dependencies..."
    if ! sudo -u "$APP_USER" ./venv/bin/pip install mysqlclient; then
        warning "mysqlclient installation failed, trying with manual flags..."
        export MYSQLCLIENT_CFLAGS=`pkg-config --cflags mysqlclient || echo "-I/usr/include/mysql"`
        export MYSQLCLIENT_LDFLAGS=`pkg-config --libs mysqlclient || echo "-L/usr/lib/x86_64-linux-gnu -lmysqlclient"`
        sudo -u "$APP_USER" ./venv/bin/pip install mysqlclient
    fi
    
    # Install remaining requirements
    sudo -u "$APP_USER" ./venv/bin/pip install -r requirements.txt
    sudo -u "$APP_USER" ./venv/bin/pip install gunicorn psycopg2-binary django-apscheduler
    
    success "Python environment ready"
}

# Configure application
configure_app() {
    log "Configuring application..."
    
    # Create .env file
    cat > "$APP_DIR/.env" << EOF
# Aperture Booking Configuration
SECRET_KEY=$SECRET_KEY
DEBUG=False
ALLOWED_HOSTS=$DOMAIN,www.$DOMAIN,localhost,127.0.0.1,$(hostname -I | awk '{print $1}')

# Database
DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@localhost:5432/$DB_NAME
DB_ENGINE=postgresql
DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
DB_HOST=localhost
DB_PORT=5432

# Email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=localhost
EMAIL_PORT=25
EMAIL_USE_TLS=False
DEFAULT_FROM_EMAIL=noreply@$DOMAIN
SERVER_EMAIL=server@$DOMAIN

# Cache (using database cache instead of Redis)
CACHE_BACKEND=django.core.cache.backends.db.DatabaseCache
CACHE_LOCATION=cache_table

# Security
SECURE_SSL_REDIRECT=$([ "$INSTALL_SSL" == "y" ] && echo "True" || echo "False")
SESSION_COOKIE_SECURE=$([ "$INSTALL_SSL" == "y" ] && echo "True" || echo "False")
CSRF_COOKIE_SECURE=$([ "$INSTALL_SSL" == "y" ] && echo "True" || echo "False")

# Application
TIME_ZONE=UTC
LANGUAGE_CODE=en-gb
LAB_NAME=Aperture Booking
ADMIN_EMAIL=$EMAIL
EOF
    
    chown "$APP_USER:$APP_USER" "$APP_DIR/.env"
    chmod 600 "$APP_DIR/.env"
    
    # Fix any Django 4.2 compatibility issues
    log "Fixing Django 4.2 compatibility..."
    if [[ -f "$APP_DIR/apply_migration_fix.sh" ]]; then
        sudo -u "$APP_USER" bash "$APP_DIR/apply_migration_fix.sh"
    else
        # Direct fix if script not found
        sudo -u "$APP_USER" sed -i 's/condition=models\.Q/check=models.Q/g' "$APP_DIR/booking/migrations/0001_initial.py"
    fi
    
    # Test Django database connection
    log "Testing Django database connection..."
    cd "$APP_DIR"
    
    # First check what's in the .env file
    log "Database configuration:"
    grep -E "DB_|DATABASE_" "$APP_DIR/.env" | while read line; do
        log "  $line"
    done
    
    # Test basic database connectivity
    log "Testing database connectivity..."
    if sudo -u "$APP_USER" ./venv/bin/python -c "
import os
import django
from django.conf import settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aperture_booking.settings')
django.setup()
from django.db import connection
try:
    with connection.cursor() as cursor:
        cursor.execute('SELECT 1')
    print('Database connection: OK')
except Exception as e:
    print(f'Database connection failed: {e}')
    exit(1)
"; then
        success "Database connection successful"
    else
        error "Database connection failed. Check configuration and try again."
    fi
    
    # Check if migrations are needed
    log "Checking database state..."
    if sudo -u "$APP_USER" ./venv/bin/python manage.py showmigrations --plan | grep -q "auth.*\[ \]"; then
        log "Database appears to be empty, running initial setup..."
        
        # Drop and recreate database to ensure clean state
        log "Resetting database for clean installation..."
        sudo -u postgres psql << EOF
DROP DATABASE IF EXISTS $DB_NAME;
CREATE DATABASE $DB_NAME OWNER $DB_USER ENCODING 'UTF8' TEMPLATE template0;
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
EOF
        
        # Grant schema privileges
        sudo -u postgres psql -d "$DB_NAME" << EOF
GRANT ALL ON SCHEMA public TO $DB_USER;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO $DB_USER;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO $DB_USER;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO $DB_USER;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO $DB_USER;
EOF
    fi
    
    # Run Django migrations
    log "Running Django migrations..."
    if sudo -u "$APP_USER" ./venv/bin/python manage.py migrate; then
        success "Django migrations completed"
    else
        error "Django migrations failed. Check logs and database configuration."
    fi
    
    # Verify Django can connect to database (simple check)
    log "Verifying Django database connection..."
    if sudo -u "$APP_USER" ./venv/bin/python manage.py check --database default; then
        success "Database connection verified"
    else
        error "Database connection verification failed"
    fi
    
    # Collect static files
    log "Collecting static files..."
    sudo -u "$APP_USER" ./venv/bin/python manage.py collectstatic --noinput
    
    # Create email templates
    log "Creating email templates..."
    sudo -u "$APP_USER" ./venv/bin/python manage.py create_email_templates || true
    
    # Run any additional Django setup commands
    log "Finalizing Django setup..."
    sudo -u "$APP_USER" ./venv/bin/python manage.py check --deploy 2>/dev/null || true
    
    # Create cache table for database caching
    log "Creating cache table..."
    sudo -u "$APP_USER" ./venv/bin/python manage.py createcachetable
    
    # Create any missing default objects
    log "Setting up default configuration..."
    sudo -u "$APP_USER" ./venv/bin/python manage.py shell -c "
# Create default LabSettings if it doesn't exist
from booking.models import LabSettings
if not LabSettings.objects.exists():
    LabSettings.objects.create(
        lab_name='Aperture Booking',
        contact_email='$EMAIL',
        allow_booking_requests=True
    )
    print('Default lab settings created')

# Ensure default groups exist
from django.contrib.auth.models import Group
lab_admin_group, created = Group.objects.get_or_create(name='Lab Admin')
if created:
    print('Lab Admin group created')
" || true
    
    success "Application configured"
}

# Setup services
setup_services() {
    log "Setting up system services..."
    
    # Gunicorn service
    cat > /etc/systemd/system/$APP_NAME.service << EOF
[Unit]
Description=Aperture Booking Gunicorn
After=network.target postgresql.service

[Service]
Type=notify
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
Environment="DJANGO_SETTINGS_MODULE=aperture_booking.settings"
EnvironmentFile=$APP_DIR/.env
ExecStartPre=/bin/mkdir -p /var/run/$APP_NAME
ExecStartPre=/bin/chown $APP_USER:$APP_USER /var/run/$APP_NAME
ExecStart=$APP_DIR/venv/bin/gunicorn \\
    --workers 3 \\
    --bind unix:/var/run/$APP_NAME/gunicorn.sock \\
    --access-logfile /var/log/$APP_NAME/access.log \\
    --error-logfile /var/log/$APP_NAME/error.log \\
    aperture_booking.wsgi:application
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

    # Scheduler service
    cat > /etc/systemd/system/$APP_NAME-scheduler.service << EOF
[Unit]
Description=Aperture Booking Scheduler
After=network.target postgresql.service

[Service]
Type=simple
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
ExecStart=$APP_DIR/venv/bin/python manage.py scheduler
Restart=always

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable --now postgresql
    
    # Clean up any existing Redis services (in case they were installed before)
    log "Cleaning up any existing Redis services..."
    systemctl stop redis-server 2>/dev/null || true
    systemctl stop redis 2>/dev/null || true
    systemctl disable redis-server 2>/dev/null || true
    systemctl disable redis 2>/dev/null || true
    systemctl unmask redis-server 2>/dev/null || true
    systemctl unmask redis 2>/dev/null || true
    # Create systemd tmpfiles configuration to recreate runtime directory on boot
    cat > /etc/tmpfiles.d/$APP_NAME.conf << EOF
# Create runtime directory for Aperture Booking
d /var/run/$APP_NAME 0755 $APP_USER $APP_USER -
EOF
    
    # Ensure run directory exists with correct ownership before starting services
    mkdir -p /var/run/$APP_NAME
    chown "$APP_USER:$APP_USER" /var/run/$APP_NAME
    chmod 755 /var/run/$APP_NAME
    
    # Clean up any existing socket files
    rm -f /var/run/$APP_NAME/gunicorn.sock
    
    systemctl enable --now $APP_NAME.service $APP_NAME-scheduler.service
    systemctl enable nginx
    
    success "Services configured"
}

# Configure Nginx
setup_nginx() {
    log "Configuring Nginx..."
    
    # Backup default config
    mv /etc/nginx/sites-enabled/default /etc/nginx/sites-available/default.backup 2>/dev/null || true
    
    cat > /etc/nginx/sites-available/$APP_NAME << EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    
    client_max_body_size 100M;
    
    location /static/ {
        alias $APP_DIR/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    location /media/ {
        alias $APP_DIR/media/;
        expires 7d;
    }
    
    location / {
        proxy_pass http://unix:/var/run/$APP_NAME/gunicorn.sock;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;
        proxy_buffering off;
    }
}
EOF
    
    ln -sf /etc/nginx/sites-available/$APP_NAME /etc/nginx/sites-enabled/
    nginx -t && systemctl reload nginx
    
    success "Nginx configured"
}

# Setup SSL
setup_ssl() {
    if [[ "$INSTALL_SSL" == "y" ]] && [[ "$DOMAIN" != "localhost" ]]; then
        log "Setting up SSL certificate..."
        certbot --nginx -d "$DOMAIN" -d "www.$DOMAIN" --non-interactive --agree-tos -m "$EMAIL"
        success "SSL certificate installed"
    fi
}

# Create admin user
create_admin() {
    log "Creating admin user..."
    
    cd "$APP_DIR"
    if [ -t 0 ]; then
        # Interactive mode
        echo
        echo "Create a superuser account for Django admin:"
        sudo -u "$APP_USER" ./venv/bin/python manage.py createsuperuser
        success "Admin user created"
    else
        # Non-interactive mode - create default admin user
        warning "Creating default admin user in non-interactive mode..."
        warning "Username: admin"
        warning "Password: admin123"
        warning "Email: $EMAIL"
        warning "IMPORTANT: Change this password immediately after login!"
        
        if sudo -u "$APP_USER" ./venv/bin/python manage.py shell -c "
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', '$EMAIL', 'admin123')
    print('Default admin user created')
else:
    print('Admin user already exists')
"; then
            log "Admin user creation completed"
        else
            warning "Admin user creation failed, you may need to create one manually"
        fi
        success "Default admin user created (username: admin, password: admin123)"
    fi
}


# Setup automatic backups
setup_backups() {
    log "Setting up automatic backups..."
    
    # Create backup script
    cat > "$APP_DIR/backup.sh" << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/aperture-booking/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="aperture-booking"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup database
pg_dump -U aperture -h localhost $DB_NAME | gzip > "$BACKUP_DIR/db_$DATE.sql.gz"

# Backup media files
tar -czf "$BACKUP_DIR/media_$DATE.tar.gz" -C /opt/aperture-booking media/

# Keep only last 30 days of backups
find "$BACKUP_DIR" -type f -mtime +30 -delete

echo "Backup completed: $DATE"
EOF
    
    chmod +x "$APP_DIR/backup.sh"
    chown "$APP_USER:$APP_USER" "$APP_DIR/backup.sh"
    
    # Add to crontab
    echo "0 2 * * * $APP_USER $APP_DIR/backup.sh >> /var/log/$APP_NAME/backup.log 2>&1" > /etc/cron.d/$APP_NAME-backup
    
    success "Automatic backups configured (daily at 2 AM)"
}

# Start services
start_services() {
    log "Starting and verifying services..."
    
    # Restart services to ensure clean state
    log "Restarting application services..."
    systemctl stop $APP_NAME.service $APP_NAME-scheduler.service 2>/dev/null || true
    sleep 2
    
    # Start services
    systemctl start $APP_NAME.service
    systemctl start $APP_NAME-scheduler.service
    
    # Reload nginx to ensure it picks up any changes
    systemctl reload nginx
    
    # Wait for services to start
    log "Waiting for services to start..."
    sleep 10
    
    # Check application service
    if systemctl is-active --quiet $APP_NAME.service; then
        success "Application service is running"
        
        # Verify socket file was created
        if [[ -S "/var/run/$APP_NAME/gunicorn.sock" ]]; then
            success "Gunicorn socket created successfully"
        else
            warning "Gunicorn socket not found, waiting longer..."
            sleep 5
            if [[ -S "/var/run/$APP_NAME/gunicorn.sock" ]]; then
                success "Gunicorn socket created (delayed)"
            else
                warning "Gunicorn socket still missing"
                log "Service logs:"
                journalctl -u $APP_NAME --no-pager -n 5
            fi
        fi
    else
        warning "Application service failed to start"
        log "Service status:"
        systemctl status $APP_NAME.service --no-pager -l
        log "Recent logs:"
        journalctl -u $APP_NAME --no-pager -n 10
    fi
    
    # Check scheduler service
    if systemctl is-active --quiet $APP_NAME-scheduler.service; then
        success "Scheduler service is running"
    else
        warning "Scheduler service failed to start"
        log "Scheduler status:"
        systemctl status $APP_NAME-scheduler.service --no-pager -l
    fi
    
    # Check nginx
    if systemctl is-active --quiet nginx; then
        success "Nginx is running"
    else
        warning "Nginx is not running"
        systemctl status nginx --no-pager -l
    fi
    
    # Final verification - test HTTP response
    log "Testing HTTP response..."
    sleep 2
    local server_ip=$(hostname -I | awk '{print $1}')
    if curl -f -s "http://localhost/" > /dev/null 2>&1; then
        success "Application is responding to HTTP requests"
    elif curl -f -s "http://$server_ip/" > /dev/null 2>&1; then
        success "Application is responding to HTTP requests on $server_ip"
    else
        warning "Application may not be responding to HTTP requests"
        log "You may need to check:"
        log "  - Service logs: journalctl -u $APP_NAME -f"
        log "  - Nginx logs: tail -f /var/log/nginx/error.log"
        log "  - Application logs: tail -f $APP_DIR/logs/*.log"
    fi
}

# Display summary
show_summary() {
    echo
    echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}            Installation Completed Successfully!             ${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
    echo
    echo -e "${BLUE}Access URLs:${NC}"
    echo -e "  Main Site:  ${GREEN}http$([ "$INSTALL_SSL" == "y" ] && echo "s")://$DOMAIN${NC}"
    if [[ "$DOMAIN" == "localhost" ]]; then
        echo -e "  IP Access:  ${GREEN}http://$(hostname -I | awk '{print $1}')${NC}"
    fi
    echo -e "  Admin Panel: ${GREEN}http$([ "$INSTALL_SSL" == "y" ] && echo "s")://$DOMAIN/admin/${NC}"
    echo
    echo -e "${BLUE}Credentials:${NC}"
    echo -e "  Database Password: ${YELLOW}$DB_PASSWORD${NC}"
    if [ -t 0 ]; then
        echo -e "  Admin Username: ${YELLOW}(as created)${NC}"
    else
        echo -e "  Admin Username: ${YELLOW}admin${NC}"
        echo -e "  Admin Password: ${YELLOW}admin123${NC} ${RED}(CHANGE IMMEDIATELY!)${NC}"
    fi
    echo
    echo -e "${BLUE}Configuration Files:${NC}"
    echo -e "  Application: ${YELLOW}$APP_DIR/.env${NC}"
    echo -e "  Nginx: ${YELLOW}/etc/nginx/sites-available/$APP_NAME${NC}"
    echo
    echo -e "${BLUE}Service Management:${NC}"
    echo -e "  Start:   ${YELLOW}systemctl start $APP_NAME${NC}"
    echo -e "  Stop:    ${YELLOW}systemctl stop $APP_NAME${NC}"
    echo -e "  Status:  ${YELLOW}systemctl status $APP_NAME${NC}"
    echo -e "  Logs:    ${YELLOW}journalctl -u $APP_NAME -f${NC}"
    echo
    echo -e "${BLUE}Backup Location:${NC} ${YELLOW}$APP_DIR/backups/${NC}"
    echo
    echo -e "${GREEN}Next Steps:${NC}"
    echo "1. Test the application at your domain"
    echo "2. Configure email settings in .env file"
    echo "3. Customize your lab settings in the admin panel"
    echo "4. Set up monitoring and alerting"
    echo
    warning "Security: Remember to update the database password in .env!"
    echo
}

# Main installation
main() {
    # Check for cleanup flag
    if [[ "$1" == "--cleanup" ]] || [[ "$1" == "-c" ]]; then
        check_root
        echo -e "${YELLOW}Cleanup Mode${NC}"
        echo "This will remove the existing Aperture Booking installation."
        echo "Directories to be removed:"
        echo "  - $APP_DIR"
        echo "  - /var/run/$APP_NAME"
        echo "  - /var/log/$APP_NAME"
        echo
        if [ -t 0 ]; then
            read -p "Are you sure you want to continue? (y/n): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 0
            fi
        fi
        
        log "Stopping services..."
        systemctl stop $APP_NAME.service $APP_NAME-scheduler.service 2>/dev/null || true
        systemctl disable $APP_NAME.service $APP_NAME-scheduler.service 2>/dev/null || true
        
        log "Removing installation..."
        rm -rf "$APP_DIR"
        rm -rf /var/run/$APP_NAME
        rm -rf /var/log/$APP_NAME
        rm -f /etc/systemd/system/$APP_NAME*.service
        rm -f /etc/nginx/sites-enabled/$APP_NAME
        rm -f /etc/nginx/sites-available/$APP_NAME
        
        systemctl daemon-reload
        systemctl reload nginx 2>/dev/null || true
        
        success "Cleanup complete. You can now run the installer again."
        exit 0
    fi
    
    show_banner
    check_root
    get_configuration
    
    log "Starting installation..."
    START_TIME=$(date +%s)
    
    detect_os
    install_dependencies
    quick_setup
    setup_database
    setup_python
    configure_app
    create_admin
    setup_services
    setup_nginx
    setup_ssl
    setup_backups
    start_services
    
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    
    show_summary
    success "Installation completed in $DURATION seconds"
}

# Run installation
main "$@"
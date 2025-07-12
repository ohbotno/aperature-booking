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
# - Redis for caching
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
APP_DIR="/opt/aperture-booking"
DOMAIN=""
EMAIL=""
DB_PASSWORD=$(openssl rand -base64 32)
SECRET_KEY=$(python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())' 2>/dev/null || openssl rand -base64 50)

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
            nginx redis-server \
            build-essential libpq-dev \
            git curl wget unzip \
            certbot python3-certbot-nginx \
            supervisor ufw fail2ban
    elif [[ "$PKG_MANAGER" == "yum" ]]; then
        yum install -y epel-release
        yum install -y \
            python3 python3-pip python3-devel \
            postgresql postgresql-server postgresql-contrib \
            nginx redis \
            gcc postgresql-devel \
            git curl wget unzip \
            certbot python3-certbot-nginx \
            supervisor firewalld fail2ban
        
        # Initialize PostgreSQL on RHEL/CentOS
        postgresql-setup initdb
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
    
    sudo -u postgres psql << EOF
CREATE USER $APP_USER WITH PASSWORD '$DB_PASSWORD';
CREATE DATABASE $APP_NAME OWNER $APP_USER;
GRANT ALL PRIVILEGES ON DATABASE $APP_NAME TO $APP_USER;
EOF
    
    success "Database configured"
}

# Python setup
setup_python() {
    log "Setting up Python environment..."
    
    cd "$APP_DIR"
    sudo -u "$APP_USER" python3 -m venv venv
    sudo -u "$APP_USER" ./venv/bin/pip install --upgrade pip wheel
    sudo -u "$APP_USER" ./venv/bin/pip install -r requirements.txt
    sudo -u "$APP_USER" ./venv/bin/pip install gunicorn psycopg2-binary redis
    
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
ALLOWED_HOSTS=$DOMAIN,www.$DOMAIN,localhost,127.0.0.1

# Database
DB_ENGINE=postgresql
DB_NAME=$APP_NAME
DB_USER=$APP_USER
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

# Redis Cache
CACHE_BACKEND=django.core.cache.backends.redis.RedisCache
CACHE_LOCATION=redis://127.0.0.1:6379/1

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
    
    # Run Django setup
    cd "$APP_DIR"
    sudo -u "$APP_USER" ./venv/bin/python manage.py migrate
    sudo -u "$APP_USER" ./venv/bin/python manage.py collectstatic --noinput
    sudo -u "$APP_USER" ./venv/bin/python manage.py create_email_templates || true
    
    success "Application configured"
}

# Setup services
setup_services() {
    log "Setting up system services..."
    
    # Gunicorn service
    cat > /etc/systemd/system/$APP_NAME.service << EOF
[Unit]
Description=Aperture Booking Gunicorn
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
ExecStart=$APP_DIR/venv/bin/gunicorn \\
    --workers 3 \\
    --bind unix:/var/run/$APP_NAME/gunicorn.sock \\
    --access-logfile /var/log/$APP_NAME/access.log \\
    --error-logfile /var/log/$APP_NAME/error.log \\
    aperture_booking.wsgi:application

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
    systemctl enable --now redis postgresql
    systemctl enable $APP_NAME.service $APP_NAME-scheduler.service
    
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
        
        sudo -u "$APP_USER" ./venv/bin/python manage.py shell << 'EOF'
from django.contrib.auth.models import User
import os
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', os.environ.get('ADMIN_EMAIL', 'admin@localhost'), 'admin123')
    print("Default admin user created")
else:
    print("Admin user already exists")
EOF
        success "Default admin user created (username: admin, password: admin123)"
    fi
}

# Setup firewall
setup_firewall() {
    log "Configuring firewall..."
    
    if command -v ufw &> /dev/null; then
        ufw --force enable
        ufw allow 22/tcp
        ufw allow 80/tcp
        ufw allow 443/tcp
        success "Firewall configured (UFW)"
    elif command -v firewall-cmd &> /dev/null; then
        systemctl enable --now firewalld
        firewall-cmd --permanent --add-service=ssh
        firewall-cmd --permanent --add-service=http
        firewall-cmd --permanent --add-service=https
        firewall-cmd --reload
        success "Firewall configured (firewalld)"
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
    log "Starting services..."
    
    systemctl start $APP_NAME.service $APP_NAME-scheduler.service
    
    # Check if services are running
    sleep 3
    if systemctl is-active --quiet $APP_NAME.service; then
        success "Application is running"
    else
        error "Application failed to start. Check logs: journalctl -u $APP_NAME"
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
    setup_services
    setup_nginx
    setup_ssl
    setup_firewall
    setup_backups
    start_services
    create_admin
    
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    
    show_summary
    success "Installation completed in $DURATION seconds"
}

# Run installation
main "$@"
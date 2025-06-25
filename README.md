# Aperture Booking Documentation

This branch contains comprehensive documentation for the Aperture Booking laboratory resource management system.

## 📚 Documentation Structure

### User Documentation
- [`user/quick-start.md`](user/quick-start.md) - Getting started guide for new users
- [`user/registration.md`](user/registration.md) - Account creation and setup
- [`user/creating-bookings.md`](user/creating-bookings.md) - Complete booking tutorial
- [`user/calendar-interface.md`](user/calendar-interface.md) - Calendar navigation and features

### Administrator Documentation  
- [`admin/system-setup.md`](admin/system-setup.md) - Initial system configuration and Site Administrator dashboard
- [`admin/resource-management.md`](admin/resource-management.md) - Managing resources and equipment
- [`admin/maintenance-management.md`](admin/maintenance-management.md) - Maintenance scheduling and tracking
- Site Administrator Features:
  - Automated backup management and scheduling
  - Update system with GitHub integration
  - User management and approval workflows
  - System monitoring and maintenance tools

### Developer Documentation
- [`developer/installation.md`](developer/installation.md) - Complete installation and deployment guide
  - Development environment setup (local installation)
  - Production deployment options (automated, Docker, manual)  
  - Docker containerization with PostgreSQL and Redis
  - Web server configuration (Nginx + Gunicorn)
  - SSL/HTTPS setup and security hardening
  - Update system and backup automation
- [`api/overview.md`](api/overview.md) - REST API documentation
- [`api/authentication.md`](api/authentication.md) - API authentication and security

### Support Documentation
- [`troubleshooting/common-issues.md`](troubleshooting/common-issues.md) - Solutions to common problems

## 🔗 Project Information

**Repository**: [ohbotno/aperture-booking](https://github.com/ohbotno/aperture-booking)
- **Main Branch**: Contains the application source code
- **Docs Branch**: Contains comprehensive documentation (this branch)

## ✨ Key Features

- **Resource Management**: Equipment booking and scheduling system
- **User Management**: Role-based access with approval workflows  
- **Maintenance Tracking**: Equipment maintenance scheduling and logging
- **Automated Backups**: Built-in backup management with scheduling
- **Update System**: GitHub-integrated automatic updates
- **Site Administration**: Comprehensive dashboard for system management
- **Production Ready**: Docker deployment with Nginx + PostgreSQL + Redis

## 📄 Project Files

The following project files are maintained here for reference:
- `PROJECT.md` - Complete project specification
- `LICENSING.md` - Dual licensing information
- `COMMERCIAL.md` - Commercial licensing details

## 🚀 Getting Started

### For Different Roles:
1. **New Users**: Start with [`user/quick-start.md`](user/quick-start.md)
2. **System Administrators**: Begin with [`admin/system-setup.md`](admin/system-setup.md)  
3. **Developers & IT Teams**: Check [`developer/installation.md`](developer/installation.md)

### Quick Installation Options:

#### Docker Deployment (Recommended)
```bash
git clone https://github.com/ohbotno/aperture-booking.git
cd aperture-booking
cp .env.example .env
# Edit .env with your configuration
docker-compose up -d
```

#### Automated Source Installation
```bash
curl -fsSL https://raw.githubusercontent.com/ohbotno/aperture-booking/main/deploy/install.sh | sudo bash
```

#### Manual Development Setup
```bash
git clone https://github.com/ohbotno/aperture-booking.git
cd aperture-booking
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

See [`developer/installation.md`](developer/installation.md) for complete deployment documentation.

## 🤝 Contributing

Documentation contributions are welcome! Please:
1. Fork this repository
2. Create a documentation branch
3. Make your improvements
4. Submit a pull request

For code contributions, work on the [`main` branch](https://github.com/ohbotno/aperture-booking/tree/main).
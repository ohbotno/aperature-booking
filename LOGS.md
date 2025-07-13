# System Logs Feature

## Overview

The Aperture Booking system includes a comprehensive system log viewer accessible through the Django admin interface. This tool focuses on infrastructure and service logs, providing visibility into server health and performance when deployed in production.

## Features

### 🔍 **Admin Log Viewer**
- Accessible at `/admin/booking/systemlogproxy/`
- Real-time log viewing and filtering
- Multiple log source integration
- Auto-refresh capability

### 📊 **Log Sources**

The system monitors infrastructure logs from:

1. **🌐 Web Server Logs**
   - `/var/log/nginx/access.log` - Main Nginx access log
   - `/var/log/nginx/error.log` - Main Nginx error log
   - `/var/log/aperture-booking/access.log` - Application-specific access logs
   - `/var/log/aperture-booking/error.log` - Application-specific error logs

2. **🔧 Service Logs (Systemd)**
   - `aperture-booking.service` - Main application service status
   - `aperture-booking-scheduler.service` - Background scheduler service
   - `nginx.service` - Web server service status
   - `postgresql.service` - Database service status
   - `ssh.service` - SSH service for remote access
   - `systemd-timesyncd.service` - Time synchronization
   - `networkd-dispatcher.service` - Network service

3. **💾 Database Logs**
   - `/var/log/postgresql/postgresql-*.log` - PostgreSQL server logs
   - Database connection issues, query errors, performance warnings

4. **🖥️ System Logs**
   - `/var/log/syslog` - General system events
   - `/var/log/auth.log` - Authentication and authorization
   - `/var/log/kern.log` - Kernel messages
   - `/var/log/dpkg.log` - Package installation/updates

### 🎛️ **Filtering Options**

- **Source**: Filter by specific log source
- **Level**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Time Range**: Last hour, 6 hours, 24 hours, week
- **Search**: Text search across log messages
- **Auto-refresh**: Automatic updates every 30 seconds

### 🔧 **Log Configuration**

#### Log Rotation
- Application logs: 10MB max, 5 backups
- Error logs: 10MB max, 5 backups  
- Security logs: 5MB max, 10 backups

#### Log Levels by Component
- **Django Framework**: INFO level
- **Booking Application**: DEBUG level (production: INFO)
- **Security Events**: INFO level
- **Scheduler**: INFO level
- **Backup Service**: INFO level

## Usage

### Accessing Logs
1. Login to Django admin as staff user
2. Navigate to "BOOKING" section
3. Click "System log proxies"
4. Use filters to find relevant logs

### Common Use Cases

#### Troubleshooting Web Server Issues
```
Source: Nginx Error Log
Level: ERROR or WARNING
Time: Last hour
```

#### Monitoring Service Health
```
Source: Aperture Service (systemd)
Level: ERROR
Time: Last 24 hours
```

#### Database Performance Issues
```
Source: PostgreSQL
Search: "slow" or "timeout"
Time: Last 6 hours
```

#### Security Monitoring
```
Source: Authentication Log
Search: "failed" or "denied"
Time: Last week
```

#### System Resource Issues
```
Source: System Log
Search: "memory" or "disk"
Level: WARNING or ERROR
```

### Emergency Debugging

If the admin interface is inaccessible, use command line:

```bash
# Check service status
sudo systemctl status aperture-booking nginx postgresql

# View service logs
sudo journalctl -u aperture-booking -f
sudo journalctl -u nginx -f

# Web server logs
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log

# System logs
sudo tail -f /var/log/syslog
sudo tail -f /var/log/auth.log

# Database logs
sudo tail -f /var/log/postgresql/postgresql-*.log
```

## File Locations

```
Web Server Logs:
/var/log/nginx/
├── access.log                    # Main web server access
├── error.log                     # Main web server errors
└── [rotated logs]               # access.log.1, error.log.1, etc.

/var/log/aperture-booking/
├── access.log                    # Application-specific access
└── error.log                     # Application-specific errors

Database Logs:
/var/log/postgresql/
└── postgresql-*.log              # PostgreSQL server logs

System Logs:
/var/log/
├── syslog                        # General system events
├── auth.log                      # Authentication logs
├── kern.log                      # Kernel messages
└── dpkg.log                      # Package management

Systemd Journals (in memory):
├── aperture-booking.service
├── aperture-booking-scheduler.service  
├── nginx.service
├── postgresql.service
├── ssh.service
└── systemd-timesyncd.service
```

## Security Notes

- Only staff users can access the log viewer
- Logs may contain sensitive information
- Log files are automatically rotated to prevent disk space issues
- Consider regular log archival for compliance requirements

## Technical Details

### Implementation
- **Log Viewer**: `booking/log_viewer.py`
- **Admin Integration**: `booking/admin.py` (SystemLogAdmin)
- **Templates**: `booking/templates/admin/booking/systemlogproxy/`
- **Settings**: Enhanced logging configuration in `settings.py`

### Dependencies
- No additional packages required
- Uses Django's built-in logging framework
- Integrates with systemd journal via `journalctl`
- File parsing with regex patterns

This logging system provides comprehensive monitoring capabilities for production deployments while maintaining security and performance.
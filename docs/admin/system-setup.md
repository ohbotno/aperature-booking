start p# Initial System Setup

This guide walks system administrators through the initial configuration of Aperture Booking after installation.

## Prerequisites

Before starting system setup, ensure you have:

- ✅ Aperture Booking installed and accessible
- ✅ Database configured and migrated
- ✅ Web server (Apache/Nginx) configured
- ✅ Email service configured (SMTP)
- ✅ Administrator account created during installation
- ✅ SSL certificate installed (recommended)

## Step 1: First Administrator Login

### Access the System
1. Navigate to your Aperture Booking URL
2. Login with the administrator credentials created during installation
3. You'll be taken to the administrator dashboard

### Verify Installation
Check that all components are working:
- **Database connectivity**: Dashboard loads without errors
- **Email service**: Test email sending in Admin > Settings
- **File uploads**: Test image upload functionality
- **Static files**: CSS and JavaScript load correctly

## Step 2: Configure About Page

The About page provides information about your facility to users.

### Access About Page Settings
1. Go to **Admin > Settings > About Page**
2. Click **"Edit About Page"** or create new if none exists

### Essential Information
Fill out the following sections:

#### Facility Information
```
Title: [Your Institution] Laboratory Booking System
Description: Brief overview of your facility and booking system purpose
```

#### Location & Contact
```
Address: Physical address of your facility
Phone: Main contact number
Email: Primary contact email for support
Website: Institution or department website
```

#### Operating Hours
```
Monday - Friday: 8:00 AM - 6:00 PM
Saturday: 9:00 AM - 2:00 PM
Sunday: Closed
```

#### Policies & Guidelines
```
- Booking cancellation policy
- No-show policy and consequences  
- Equipment usage guidelines
- Safety requirements
- Contact information for emergencies
```

#### Upload Images
- **Logo**: Your institution/department logo
- **Facility Photos**: Images of labs, equipment, common areas
- **Equipment Photos**: Will be added when creating resources

## Step 3: Configure Academic Structure

Set up your institution's organizational hierarchy.

### Faculties
1. Go to **Admin > Academic Structure > Faculties**
2. Click **"Add Faculty"**
3. Add each faculty in your institution:
   ```
   Examples:
   - Faculty of Science
   - Faculty of Engineering  
   - Faculty of Medicine
   - Faculty of Arts & Humanities
   ```

### Colleges
1. Go to **Admin > Academic Structure > Colleges**
2. For each faculty, add relevant colleges:
   ```
   Example (Faculty of Science):
   - College of Physical Sciences
   - College of Life Sciences
   - College of Computer Science
   ```

### Departments
1. Go to **Admin > Academic Structure > Departments**
2. Add departments within each college:
   ```
   Example (College of Life Sciences):
   - Biology Department
   - Chemistry Department
   - Environmental Science Department
   ```

## Step 4: Configure Email Templates

Customize email notifications sent to users.

### Access Email Templates
1. Go to **Admin > Communications > Email Templates**
2. Review and customize each template type

### Template Types
Configure these essential templates:

#### Welcome Email
- **Subject**: Welcome to [Institution] Lab Booking
- **Content**: Welcome message, getting started instructions
- **Variables**: `{user_name}`, `{institution_name}`, `{login_url}`

#### Booking Confirmation
- **Subject**: Booking Confirmed: {booking_title}
- **Content**: Booking details, check-in instructions
- **Variables**: `{booking_title}`, `{resource_name}`, `{start_time}`, `{end_time}`

#### Booking Reminder
- **Subject**: Reminder: {booking_title} in 24 hours
- **Content**: Upcoming booking reminder
- **Variables**: All booking-related variables

#### Access Request Notifications
- **Subject**: New Access Request: {resource_name}
- **Content**: Notification for administrators
- **Variables**: `{user_name}`, `{resource_name}`, `{request_reason}`

#### Training Notifications
- **Subject**: Training Required: {resource_name}
- **Content**: Training requirements and instructions
- **Variables**: `{resource_name}`, `{training_courses}`, `{deadline}`

## Step 5: Create User Roles and Permissions

Configure user roles appropriate for your institution.

### Default User Roles
Review and customize these default roles:

#### Student
- **Permissions**: Create bookings, view public resources
- **Restrictions**: Limited booking duration, approval required for some resources
- **Typical Users**: Undergraduate and graduate students

#### Academic
- **Permissions**: Extended booking privileges, group management
- **Restrictions**: None for standard resources
- **Typical Users**: Faculty, lecturers, professors

#### Researcher  
- **Permissions**: Advanced booking features, longer booking windows
- **Restrictions**: May need approval for expensive equipment
- **Typical Users**: Research staff, postdocs, visiting researchers

#### Lab Tech
- **Permissions**: Equipment maintenance, booking oversight
- **Restrictions**: Cannot modify system settings
- **Typical Users**: Laboratory technicians, support staff

#### Sysadmin
- **Permissions**: Full system access, user management
- **Restrictions**: None
- **Typical Users**: IT staff, system administrators

### Custom Roles
Create additional roles as needed:
1. Go to **Admin > User Management > Groups**
2. Create custom groups with specific permissions
3. Assign users to appropriate groups

## Step 6: Configure System Settings

Set global system preferences.

### General Settings
1. Go to **Admin > Settings > General**
2. Configure:

```
System Name: [Your Institution] Laboratory Booking
Default Timezone: [Your local timezone]
Date Format: DD/MM/YYYY or MM/DD/YYYY
Time Format: 24-hour or 12-hour
Language: English (or your primary language)
```

### Booking Settings
```
Default Booking Duration: 2 hours
Maximum Booking Duration: 8 hours
Advance Booking Limit: 30 days
Cancellation Deadline: 24 hours
No-Show Grace Period: 15 minutes
```

### Notification Settings
```
Email From Address: noreply@yourinstitution.edu
Email From Name: [Institution] Lab Booking
Daily Digest Time: 8:00 AM
Weekly Digest Day: Monday
Emergency Alert Method: Email + SMS (if configured)
```

### Calendar Settings
```
Business Hours Start: 8:00 AM
Business Hours End: 6:00 PM
Working Days: Monday - Friday
Calendar Color Theme: [Select appropriate colors]
Export Format: ICS (iCalendar)
```

## Step 7: Set Up Resources

Create your first resources to test the system.

### Resource Categories
Create logical categories:
```
Examples:
- Microscopy Equipment
- Analytical Instruments  
- General Lab Equipment
- Meeting Rooms
- Specialized Facilities
```

### Create Test Resources
Add a few test resources:

#### Example: PCR Machine
```
Name: PCR Machine #1
Type: Equipment
Location: Lab A-101
Description: High-throughput PCR system for molecular biology
Capacity: 1 user
Booking Duration: 30 minutes - 4 hours
Advance Notice: 2 hours
Training Required: Yes
Approval Required: No
```

#### Example: Conference Room
```
Name: Conference Room B
Type: Room
Location: Building B, Floor 2
Description: Meeting room with presentation equipment
Capacity: 8 people
Booking Duration: 30 minutes - 8 hours
Advance Notice: 30 minutes
Training Required: No
Approval Required: No
```

## Step 8: Configure Approval Workflows

Set up approval processes for resource access.

### Access Request Rules
1. Go to **Admin > Approval System > Access Rules**
2. Create rules for different resource types:

#### High-Value Equipment
```
Trigger: Resource value > £10,000
Approval Required: Yes
Approvers: Lab Manager + Department Head
Training Required: Mandatory
Risk Assessment: Required
```

#### Student Access
```
Trigger: User role = Student
Approval Required: Yes for specialized equipment
Approvers: Course Instructor or Supervisor
Training Required: Basic safety training
```

#### External Users
```
Trigger: User from external institution
Approval Required: Always
Approvers: Facility Manager
Training Required: All safety courses
Insurance: Required
```

### Training Requirements
1. Go to **Admin > Training > Courses**
2. Create mandatory training courses:

```
Examples:
- General Lab Safety (Required for all users)
- Chemical Safety (Required for chemistry equipment)
- Biological Safety (Required for biological equipment)
- Equipment-Specific Training (Per specialized instrument)
```

## Step 9: Set Up Maintenance Management

Configure maintenance tracking for your resources.

### Maintenance Vendors
1. Go to **Admin > Maintenance > Vendors**
2. Add your service providers:

```
Example Vendor:
Name: Scientific Equipment Services Ltd
Contact: John Smith
Email: service@equipment-services.com
Phone: +44 123 456 7890
Specialties: Microscopy, Spectroscopy
Hourly Rate: £85
Emergency Rate: £150
Response SLA: 4 hours
```

### Maintenance Schedules
Set up preventive maintenance:
1. Go to **Admin > Maintenance > Schedules**
2. Create recurring maintenance tasks:

```
Example Schedule:
Resource: PCR Machine #1
Type: Preventive
Frequency: Every 3 months
Duration: 2 hours
Assigned Vendor: Scientific Equipment Services Ltd
Description: Calibration and cleaning cycle
```

## Step 10: Configure Notifications

Set up the notification system.

### Email Configuration
Verify email settings:
1. Go to **Admin > Settings > Email**
2. Test email delivery:
   ```
   SMTP Server: [Your SMTP server]
   Port: 587 (TLS) or 465 (SSL)
   Username: [SMTP username]
   Password: [SMTP password]
   ```

### Notification Types
Enable appropriate notifications:
- ✅ Booking confirmations
- ✅ Booking reminders (24 hours, 1 hour)
- ✅ Cancellation notifications
- ✅ Access request updates
- ✅ Maintenance alerts
- ✅ System announcements

### Push Notifications (Optional)
If push notifications are configured:
1. Set up VAPID keys
2. Configure service worker
3. Test push delivery

## Step 11: Import Initial Data

Load existing data if migrating from another system.

### User Import
1. Go to **Admin > User Management > Import**
2. Download the CSV template
3. Format your user data:
   ```
   email,first_name,last_name,role,faculty,department,student_id
   john.doe@uni.edu,John,Doe,student,Science,Biology,S123456
   ```
4. Upload and review import results

### Resource Import
Import existing equipment:
1. Prepare resource data in CSV format
2. Include all required fields
3. Import and verify data accuracy

## Step 12: Testing and Validation

Thoroughly test the system before going live.

### Create Test Accounts
Create test accounts for each user role:
```
student.test@yourinstitution.edu (Student)
academic.test@yourinstitution.edu (Academic)  
researcher.test@yourinstitution.edu (Researcher)
tech.test@yourinstitution.edu (Lab Tech)
```

### Test Core Workflows
1. **User Registration**: Test self-registration process
2. **Booking Creation**: Create bookings with each test account
3. **Approval Process**: Test access requests and approvals
4. **Calendar Integration**: Export calendars and test external sync
5. **Email Notifications**: Verify all email types are sent correctly
6. **Maintenance Scheduling**: Create test maintenance records

### Load Testing
Test system performance:
- Multiple concurrent users
- Large numbers of bookings
- Peak usage scenarios
- Database performance under load

## Step 13: User Training and Documentation

Prepare for user onboarding.

### Training Materials
Create institution-specific training materials:
- Quick start guide with your resources
- Video tutorials for common tasks
- Lab-specific policies and procedures
- Contact information for support

### Training Sessions
Plan user training sessions:
- **Administrators**: Advanced features and management
- **Lab Technicians**: Daily operations and maintenance
- **Academic Staff**: Group management and oversight
- **Students**: Basic booking and calendar usage

### Support Documentation
Prepare support materials:
- FAQ for common issues
- Troubleshooting guide
- Contact information for different types of support
- Escalation procedures for urgent issues

## Step 14: Go-Live Checklist

Final preparations before launching to users.

### Technical Checklist
- [ ] SSL certificate installed and working
- [ ] Database backups configured and tested
- [ ] Email delivery tested and working
- [ ] All core features tested and validated
- [ ] Performance monitoring in place
- [ ] Error logging configured
- [ ] Security scanning completed

### Content Checklist  
- [ ] About page complete with institution information
- [ ] All email templates customized
- [ ] Academic structure fully configured
- [ ] Initial resources created and tested
- [ ] User roles and permissions configured
- [ ] Approval workflows tested
- [ ] Maintenance system configured

### User Readiness Checklist
- [ ] User documentation prepared
- [ ] Training sessions scheduled
- [ ] Support procedures established
- [ ] Help desk contact information distributed
- [ ] Announcement materials prepared
- [ ] Migration timeline communicated

## Post-Launch Activities

After going live, monitor and optimize the system.

### First Week
- Monitor system performance and user adoption
- Address any immediate technical issues
- Collect user feedback and common questions
- Adjust configurations based on real usage patterns

### First Month
- Review booking patterns and resource utilization
- Analyze user behavior and system usage
- Fine-tune approval workflows and permissions
- Plan additional training sessions as needed

### Ongoing Maintenance
- Regular system updates and security patches
- Database maintenance and optimization
- User feedback collection and feature requests
- Continuous improvement of processes and workflows

## Getting Help

### Aperture Booking Support
- **Documentation**: Complete documentation available
- **Community Forum**: User community and discussions
- **Email Support**: Technical support for commercial licenses
- **Professional Services**: Implementation and customization assistance

### System Administration
- **Log Files**: Monitor application and server logs
- **Health Checks**: Built-in system health monitoring
- **Performance Metrics**: Track system performance and usage
- **Backup Verification**: Regular backup testing and verification

---

**Congratulations!** Your Aperture Booking system is now configured and ready for users. Regular monitoring and maintenance will ensure optimal performance and user satisfaction.

*Next: [User Management Guide](user-management.md) to learn about managing users and permissions*
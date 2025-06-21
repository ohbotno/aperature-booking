# Resource Management Guide

Comprehensive guide for administrators to create, configure, and manage laboratory resources in Aperture Booking.

## Overview

Resource management is at the heart of Aperture Booking. This guide covers everything from creating basic resources to implementing advanced approval workflows and training requirements.

### What are Resources?
Resources in Aperture Booking represent any bookable item:
- **Equipment**: Microscopes, analyzers, instruments
- **Rooms**: Labs, meeting rooms, study spaces
- **Facilities**: Shared workspaces, specialized areas
- **Services**: Consultations, training sessions

### Resource Lifecycle
1. **Creation**: Add new resources to the system
2. **Configuration**: Set booking rules and requirements
3. **Activation**: Make available for booking
4. **Management**: Ongoing updates and maintenance
5. **Retirement**: Remove from active use

## Creating Resources

### Basic Resource Creation

#### Access Resource Management
1. Go to **Admin > Resources > Add Resource**
2. Or use **"Quick Add"** from the dashboard
3. Complete the resource creation form

#### Required Information

##### Basic Details
```
Name: Descriptive, unique name for the resource
  Examples:
  - "PCR Machine #1" (for equipment)
  - "Conference Room A" (for rooms)
  - "Microscopy Lab" (for facilities)

Description: Detailed information about the resource
  Include:
  - Capabilities and specifications
  - Usage guidelines
  - Safety considerations
  - Contact information for questions
```

##### Resource Classification
```
Resource Type: Category of resource
  - Equipment: Individual instruments or devices
  - Room: Enclosed spaces for meetings or work
  - Facility: Larger areas or specialized spaces
  - Service: Bookable services or consultations

Location: Physical location of the resource
  Format: Building-Room (e.g., "Science-101", "Lab A-204")
  Include: Floor and any specific location details
```

##### Capacity and Usage
```
Capacity: Maximum number of simultaneous users
  Examples:
  - 1 person (individual equipment)
  - 8 people (conference room)
  - 20 people (teaching lab)

Usage Notes: Specific information about proper use
  Include safety requirements, operating procedures
```

### Advanced Resource Configuration

#### Booking Constraints
```
Minimum Booking Duration: Shortest allowed booking
  Examples:
  - 15 minutes (quick consultations)
  - 30 minutes (standard equipment)
  - 1 hour (complex procedures)

Maximum Booking Duration: Longest allowed single booking
  Examples:
  - 4 hours (intensive analysis)
  - 8 hours (day-long experiments)
  - 24 hours (long-running processes)

Advance Booking Window: How far ahead bookings can be made
  Examples:
  - 30 days (standard equipment)
  - 90 days (high-demand resources)
  - 7 days (walk-in friendly equipment)

Minimum Advance Notice: Required lead time for bookings
  Examples:
  - Immediate (available for walk-ins)
  - 2 hours (preparation time needed)
  - 24 hours (scheduling coordination required)
```

#### Operating Hours
```
Business Hours: When the resource is normally available
  Standard: Monday-Friday, 8:00 AM - 6:00 PM
  Extended: Monday-Sunday, 6:00 AM - 10:00 PM
  24/7: Always available (with appropriate access)

Holiday Schedule: Availability during institutional holidays
  Options:
  - Follow institutional calendar
  - Custom holiday schedule
  - Always available
  - Always closed

Timezone: Local timezone for the resource
  Important for multi-campus institutions
```

### Resource Images and Documentation

#### Adding Images
1. **Primary Image**: Main photo shown in resource listings
   - High-quality photo of the equipment/room
   - Good lighting and clear view
   - Standard orientation (landscape preferred)

2. **Additional Photos**: Gallery of supplementary images
   - Different angles and views
   - Control panels or interfaces
   - Usage examples
   - Safety features

3. **Image Guidelines**
   ```
   Recommended Specifications:
   - Format: JPEG or PNG
   - Resolution: 1920x1080 pixels minimum
   - File Size: Under 5MB each
   - Aspect Ratio: 16:9 or 4:3 preferred
   ```

#### Documentation Attachments
- **User Manuals**: Operating instructions and procedures
- **Safety Guidelines**: Required safety protocols
- **Training Materials**: Educational resources
- **Specifications**: Technical specifications and capabilities
- **Contact Information**: Resource managers and support contacts

## Access Control and Permissions

### User Role Permissions

#### Default Access Levels
```
Student Access:
- Basic equipment: Allowed with training
- Teaching labs: Allowed during class hours
- High-value equipment: Requires approval
- Research facilities: Supervisor approval required

Academic/Researcher Access:
- Most equipment: Direct access after training
- Specialized equipment: May require approval
- Administrative rights: For owned resources
- Group booking: Can book for research teams

Lab Technician Access:
- All standard equipment: Full access
- Maintenance mode: Can block resources
- User assistance: Can modify others' bookings
- Equipment status: Can update availability

Administrator Access:
- All resources: Complete access and control
- Configuration: Can modify all settings
- User management: Grant/revoke access
- System maintenance: Emergency overrides
```

### Training Requirements

#### Setting Up Training Requirements
1. **Access Training Configuration**
   - Go to **Admin > Resources > [Resource Name] > Training**
   - Click **"Add Training Requirement"**

2. **Configure Training Courses**
   ```
   Required Courses:
   - General Lab Safety (All users)
   - Equipment-Specific Training (Per resource)
   - Chemical Safety (Chemistry equipment)
   - Biological Safety (Biology equipment)
   - Radiation Safety (Specialized equipment)
   ```

3. **Training Validation**
   ```
   Validation Methods:
   - Online Course Completion
   - In-Person Training Session
   - Competency Assessment
   - Supervisor Sign-off
   - Annual Recertification
   ```

#### Training Workflow
```
Training Process:
1. User requests access to resource
2. System checks training requirements
3. User completes required training
4. Training completion is verified
5. User gains access to resource
6. Periodic recertification as needed
```

### Approval Workflows

#### Creating Approval Rules
1. **Access Approval Configuration**
   - Go to **Admin > Approval Rules > Add Rule**
   - Select target resources and user criteria

2. **Approval Triggers**
   ```
   Trigger Conditions:
   - User Role: Students, external users, etc.
   - Resource Value: High-cost equipment
   - Usage Duration: Extended bookings
   - Time Period: After-hours usage
   - Resource Type: Specialized equipment
   ```

3. **Approval Hierarchy**
   ```
   Approval Levels:
   - Level 1: Resource responsible person
   - Level 2: Department supervisor
   - Level 3: Facility manager
   - Emergency: 24/7 emergency contact
   ```

#### Approval Process Configuration
```
Approval Workflow Example:
1. Student requests access to electron microscope
2. System requires:
   - Equipment training completion
   - Supervisor approval
   - Safety assessment completion
3. Notifications sent to:
   - Student (request received)
   - Supervisor (approval needed)
   - Equipment manager (FYI)
4. Approval decision triggers:
   - Access granted notification
   - Calendar permissions updated
   - Training schedule coordination
```

## Resource Categories and Organization

### Creating Resource Categories

#### Hierarchical Organization
```
Category Structure Example:
Science Equipment/
├── Microscopy/
│   ├── Light Microscopes
│   ├── Electron Microscopes
│   └── Specialized Imaging
├── Analytical Instruments/
│   ├── Spectroscopy
│   ├── Chromatography
│   └── Mass Spectrometry
└── General Lab Equipment/
    ├── Centrifuges
    ├── Incubators
    └── Basic Tools
```

#### Category Management
1. **Create Categories**
   - Go to **Admin > Resources > Categories**
   - Click **"Add Category"**
   - Set parent category for hierarchy

2. **Category Properties**
   ```
   Category Configuration:
   - Name: Descriptive category name
   - Description: Purpose and contents
   - Icon: Visual identifier
   - Color: Color coding for visual organization
   - Default Settings: Inherited by new resources
   ```

### Resource Tagging and Search

#### Tagging System
```
Tag Categories:
- Equipment Type: PCR, Microscope, Centrifuge
- Capabilities: High-resolution, Automated, Portable
- Applications: Research, Teaching, Service
- Safety Level: BSL-1, BSL-2, Chemical, Radiation
- Manufacturer: Zeiss, Thermo, Applied Biosystems
```

#### Search Optimization
```
Search Features:
- Full-text search across all resource fields
- Tag-based filtering
- Location-based search
- Availability filtering
- Advanced search with multiple criteria
```

## Resource Status Management

### Availability States

#### Standard States
```
Available: Normal operating condition
- Bookable by authorized users
- All features functional
- Regular maintenance up to date

Maintenance: Temporary unavailability
- Scheduled preventive maintenance
- Repair work in progress
- Cannot be booked during maintenance

Out of Service: Extended unavailability
- Major repairs needed
- Safety issues identified
- Equipment retirement pending

Reserved: Restricted availability
- Dedicated to specific project
- Limited user access
- Special approval required
```

#### Status Change Workflow
1. **Update Resource Status**
   - Go to **Admin > Resources > [Resource] > Status**
   - Select new status and provide reason
   - Set expected return to service date

2. **Automatic Notifications**
   ```
   Notification Recipients:
   - Users with existing bookings
   - Users on waiting lists
   - Resource responsible persons
   - Department administrators
   ```

3. **Impact Management**
   ```
   Status Change Actions:
   - Cancel conflicting bookings
   - Notify affected users
   - Suggest alternative resources
   - Update calendar displays
   - Log status change history
   ```

### Maintenance Scheduling

#### Preventive Maintenance
```
Maintenance Types:
- Daily: Basic cleaning and checks
- Weekly: Calibration and minor maintenance
- Monthly: Comprehensive service
- Quarterly: Major maintenance and updates
- Annual: Complete overhaul and certification
```

#### Maintenance Integration
- **Automatic Booking Blocks**: Maintenance periods block regular bookings
- **User Notifications**: Advance warning of upcoming maintenance
- **Alternative Suggestions**: Recommend substitute resources
- **Progress Tracking**: Monitor maintenance completion status

## Resource Analytics and Reporting

### Usage Analytics

#### Key Metrics
```
Utilization Metrics:
- Usage Rate: Percentage of available time booked
- User Diversity: Number of unique users
- Booking Patterns: Peak usage times and days
- Average Session: Typical booking duration
- No-Show Rate: Percentage of unused bookings
```

#### Performance Dashboard
```
Dashboard Widgets:
- Real-time availability status
- Today's booking schedule
- Usage trends (week/month/year)
- Top users and applications
- Maintenance schedule overview
```

### Reporting Features

#### Standard Reports
```
Available Reports:
- Resource Utilization Summary
- User Access Report
- Maintenance Cost Analysis
- Training Completion Status
- Booking Pattern Analysis
```

#### Custom Reports
1. **Report Builder**
   - Drag-and-drop report designer
   - Custom date ranges and filters
   - Multiple chart and table formats
   - Export to PDF, Excel, CSV

2. **Scheduled Reports**
   - Automatic generation and delivery
   - Email distribution lists
   - Regular management updates
   - Compliance reporting

## Advanced Resource Features

### Resource Groups and Dependencies

#### Linked Resources
```
Resource Relationships:
- Equipment Sets: Multiple items used together
- Room + Equipment: Room includes specific equipment
- Primary + Backup: Automatic failover options
- Sequential Usage: Workflow-based resource chains
```

#### Group Booking Management
```
Group Features:
- Single booking for multiple resources
- Automatic conflict resolution
- Coordinated scheduling
- Bulk operations and modifications
```

### Integration Capabilities

#### External Systems
```
Integration Options:
- Laboratory Information Management Systems (LIMS)
- Equipment monitoring systems
- Facility management software
- Enterprise resource planning (ERP)
- Financial systems for cost tracking
```

#### API Access
```
API Capabilities:
- Real-time availability checking
- Programmatic booking creation
- Status updates and notifications
- Usage data extraction
- Maintenance scheduling
```

### Mobile Resource Management

#### Mobile Features
```
Mobile Capabilities:
- QR code resource identification
- Quick status updates
- Mobile booking creation
- Check-in/check-out functionality
- Emergency contact access
```

#### Field Management
```
On-Site Features:
- Location-based resource discovery
- Quick problem reporting
- Status updates from mobile devices
- Photo documentation
- Maintenance request submission
```

## Best Practices

### Resource Creation Guidelines

#### Naming Conventions
```
Naming Best Practices:
✅ Good Examples:
- "PCR Machine #1 (Lab A-101)"
- "Conference Room B (2nd Floor)"
- "Zeiss LSM 880 Confocal Microscope"

❌ Avoid:
- "Equipment 1"
- "Room"
- "The Big Microscope"
```

#### Description Standards
```
Description Template:
1. Primary purpose and capabilities
2. Key specifications and features
3. Operating procedures summary
4. Safety requirements
5. Contact information for questions
6. Training requirements
7. Special scheduling notes
```

### Access Control Best Practices

#### Security Principles
```
Access Control Guidelines:
- Principle of Least Privilege: Minimum necessary access
- Role-Based Access: Use established user roles
- Regular Review: Periodic access audits
- Training Requirements: Mandatory for high-risk equipment
- Documentation: Clear approval criteria
```

#### Training Management
```
Training Best Practices:
- Standardized Curriculum: Consistent training content
- Competency Assessment: Verify understanding
- Record Keeping: Maintain training records
- Refresher Training: Periodic recertification
- Multi-Modal Learning: Online + hands-on training
```

### Maintenance Optimization

#### Preventive Maintenance
```
Maintenance Strategy:
- Manufacturer Recommendations: Follow service schedules
- Usage-Based Scheduling: Adjust frequency based on use
- Condition Monitoring: Track performance indicators
- Cost-Benefit Analysis: Balance cost vs. availability
- Vendor Relationships: Maintain service contracts
```

#### Performance Monitoring
```
Monitoring Metrics:
- Uptime Percentage: Availability reliability
- Mean Time Between Failures (MTBF)
- Mean Time To Repair (MTTR)
- User Satisfaction Scores
- Maintenance Cost Trends
```

## Troubleshooting Common Issues

### Resource Access Problems

#### Users Cannot Book Resources
**Symptoms:** Error messages when attempting to book
**Common Causes:**
- Missing training requirements
- Insufficient user permissions
- Resource is out of service
- Booking outside operating hours

**Solutions:**
1. Check user training status
2. Verify user role permissions
3. Confirm resource availability status
4. Review booking time constraints

#### Training Not Recognized
**Symptoms:** System shows training incomplete despite completion
**Common Causes:**
- Training not marked complete in system
- Wrong training course completed
- Instructor hasn't approved completion
- System synchronization delay

**Solutions:**
1. Verify completion status in training system
2. Contact training administrator
3. Check for pending approvals
4. Manually update training records if necessary

### Resource Configuration Issues

#### Booking Rules Not Working
**Symptoms:** Users can book outside configured constraints
**Common Causes:**
- Rule configuration errors
- Override permissions enabled
- Conflicting rules
- System cache issues

**Solutions:**
1. Review rule configuration
2. Check for administrator overrides
3. Clear system cache
4. Test with different user roles

#### Calendar Integration Problems
**Symptoms:** Resources not appearing in calendar views
**Common Causes:**
- Resource not marked as active
- Category filters applied
- Permission restrictions
- Display settings issues

**Solutions:**
1. Verify resource active status
2. Clear calendar filters
3. Check user permissions
4. Reset calendar view preferences

### Performance Issues

#### Slow Resource Loading
**Symptoms:** Long delays when viewing resource pages
**Common Causes:**
- Large image files
- Too many attached documents
- Database performance issues
- Network connectivity problems

**Solutions:**
1. Optimize image file sizes
2. Archive old documents
3. Contact system administrator
4. Check network connection

## Getting Help

### Support Resources
- **User Documentation**: Complete guides for end users
- **Video Tutorials**: Step-by-step video instructions
- **Webinars**: Regular training sessions for administrators
- **User Community**: Forums and discussion groups

### Technical Support
- **Help Desk**: For immediate technical issues
- **Professional Services**: For complex configuration needs
- **Custom Development**: For specialized requirements
- **Training Services**: For administrator certification

---

**Effective resource management creates a smooth, efficient booking experience for all users while maintaining proper access controls and safety requirements.** Regular review and optimization of resource configurations ensures optimal system performance.

*Next: [User Management Guide](user-management.md) to learn about managing user accounts, roles, and permissions*
# Creating Bookings

Learn how to create, modify, and manage your resource bookings effectively.

## Overview

Creating a booking reserves a resource for your use during a specific time period. This guide covers all aspects of the booking process, from simple one-time bookings to complex recurring schedules.

## Ways to Create Bookings

### Method 1: From the Calendar

This is the most intuitive way to create bookings.

1. **Navigate to the Calendar**
   - Click **"Calendar"** in the main menu
   - Choose your preferred view (Month, Week, or Day)

2. **Select a Time Slot**
   - Click on an empty time slot
   - The booking form will open with the time pre-filled

3. **Complete the Booking Form** (see detailed form guide below)

### Method 2: From Resource Pages

When you know which resource you need:

1. **Browse Resources**
   - Go to **"Resources"** in the main menu
   - Find your desired resource by browsing or searching

2. **View Resource Details**
   - Click on the resource name
   - Review availability and requirements

3. **Click "Book This Resource"**
   - The booking form opens with the resource pre-selected
   - Choose your preferred time slot

### Method 3: Using Booking Templates

For frequently repeated bookings:

1. **Access Your Templates**
   - Go to **"My Bookings"** → **"Templates"**
   - Or click **"New Booking"** → **"Use Template"**

2. **Select a Template**
   - Choose from your saved templates
   - The form pre-fills with template data

3. **Adjust as Needed**
   - Modify dates, times, or other details
   - Save as a new template if desired

## Booking Form Guide

### Required Information

#### Basic Details
- **Title**: Descriptive name for your booking
  ```
  Good examples:
  - "PCR Analysis - Project Alpha"
  - "Microscopy Session - Cell Cultures"
  - "Team Meeting - Weekly Sync"
  
  Avoid:
  - "Booking"
  - "Lab work"
  - "Meeting"
  ```

- **Resource**: The equipment or room you're booking
  - Select from the dropdown list
  - Only available resources are shown

- **Start Date & Time**: When you need the resource
  - Use the date picker for dates
  - Time picker shows available slots in green

- **End Date & Time**: When you'll finish using the resource
  - Must be after start time
  - Respects resource's maximum booking duration

#### Optional Details

- **Description**: Additional information about your work
  ```
  Helpful descriptions:
  - "Running PCR for 24 samples, project code ABC123"
  - "Training session for 3 new lab members"
  - "Urgent analysis for thesis deadline"
  ```

- **Attendees**: Others who will use the resource with you
  - Start typing names to find users
  - Specify their role (Participant, Observer, Trainer)
  - Attendees receive notification emails

### Advanced Options

#### Recurring Bookings
For regular activities, create recurring patterns:

1. **Enable Recurring**
   - Check **"Make this a recurring booking"**
   - Choose frequency: Daily, Weekly, Monthly, or Custom

2. **Set Pattern Details**
   - **Daily**: Every N days, weekdays only, or specific days
   - **Weekly**: Which days of the week, every N weeks
   - **Monthly**: Same date each month, or relative (e.g., "first Monday")
   - **Custom**: Advanced patterns with multiple rules

3. **Set End Condition**
   - **End Date**: Specify when to stop creating bookings
   - **Number of Occurrences**: Create exactly N bookings
   - **No End Date**: Continue indefinitely (not recommended)

#### Booking Dependencies
Link related bookings that must happen in sequence:

1. **Add Prerequisites**
   - Click **"Add Dependency"**
   - Select bookings that must complete first
   - Choose dependency type:
     - **Sequential**: Must complete in order
     - **Parallel**: Can run simultaneously after prerequisites
     - **Conditional**: Only book if prerequisites succeed

2. **Dependency Examples**
   ```
   Sample Preparation → PCR Analysis → Data Analysis
   (Sequential dependencies)
   
   Equipment Training → Independent Usage
   (Prerequisite dependency)
   
   Project Meeting → Lab Work (multiple parallel sessions)
   (Parallel dependencies after meeting)
   ```

### Form Validation

The system validates your booking in real-time:

#### Time Validation
- ✅ **Available Slot**: Time is free for the resource
- ⚠️ **Partial Conflict**: Overlaps with existing booking
- ❌ **Full Conflict**: Time completely unavailable
- ⏰ **Outside Hours**: Outside resource's operating hours

#### Permission Validation
- ✅ **Access Granted**: You can book this resource
- 🔐 **Approval Required**: Booking needs approval
- 📚 **Training Required**: Complete training first
- 🚫 **Access Denied**: You cannot book this resource

#### Duration Validation
- ✅ **Valid Duration**: Within resource limits
- ⚠️ **Too Short**: Below minimum booking time
- ⚠️ **Too Long**: Exceeds maximum booking time
- 📅 **Advance Notice**: Meets minimum advance booking time

## Handling Conflicts

When your desired time isn't available:

### Automatic Suggestions
The system suggests alternative times:
- **Next Available**: Earliest available slot
- **Same Day Options**: Other times on the same day
- **Similar Duration**: Slots matching your requested length
- **Nearby Resources**: Alternative resources with availability

### Conflict Resolution Options

#### 1. Choose Alternative Time
- Review suggested alternatives
- Click on a suggested slot to use it
- Adjust your schedule to fit available times

#### 2. Join Waiting List
- Click **"Join Waiting List"** for your preferred time
- Set your priority and flexibility preferences:
  ```
  Flexibility Options:
  - Exact time only
  - ±30 minutes from preferred time
  - ±1 hour from preferred time
  - Any time on the same day
  ```

#### 3. Request Access
For restricted resources:
- Click **"Request Access"**
- Complete the access request form
- Specify why you need access
- Wait for approval before booking

#### 4. Split Booking
For long bookings that don't fit:
- Divide into multiple shorter sessions
- Use sequential dependencies to link them
- Book the earliest available slots

## Special Booking Types

### Equipment Training Sessions
For learning to use new equipment:

1. **Find Training Bookings**
   - Look for resources marked "Training Available"
   - Check the resource page for training schedules

2. **Request Training**
   - Click **"Request Training"**
   - Choose from available training slots
   - Specify your experience level

3. **Complete Training**
   - Attend the training session
   - Complete any required assessments
   - Gain independent access to the equipment

### Group Bookings
For team activities or classes:

1. **Create the Booking**
   - Use a descriptive title indicating it's for a group
   - Set appropriate duration for group activities

2. **Add All Attendees**
   - Add team members as attendees
   - Specify roles (Participant, Observer, Trainer)
   - Include external attendees if allowed

3. **Set Group Permissions**
   - Enable **"Allow attendees to modify"** if appropriate
   - Set up shared responsibility for the booking

### Maintenance Bookings
For lab technicians and administrators:

1. **Access Maintenance Mode**
   - Go to **"Admin"** → **"Maintenance"** (if you have permissions)
   - Click **"Schedule Maintenance"**

2. **Complete Maintenance Form**
   - **Type**: Preventive, Corrective, Emergency, or Upgrade
   - **Description**: Detailed work description
   - **Vendor**: Assign to internal staff or external vendor
   - **Impact**: Whether it blocks other bookings

3. **Notification Settings**
   - Auto-notify affected users
   - Send advance warnings for planned maintenance
   - Set up completion notifications

## Booking Templates

Save time by creating reusable booking templates.

### Creating Templates

1. **From Existing Booking**
   - Go to any booking details page
   - Click **"Save as Template"**
   - Give the template a descriptive name

2. **From Scratch**
   - Go to **"My Bookings"** → **"Templates"**
   - Click **"New Template"**
   - Fill out the template form

### Template Fields
Templates can save:
- **Resource**: Pre-select your common equipment
- **Duration**: Standard booking length
- **Title Pattern**: Template for naming bookings
- **Description**: Standard description with placeholders
- **Attendees**: Regular team members
- **Recurring Pattern**: Standard meeting schedules

### Using Templates

1. **Quick Booking**
   - Click **"New Booking"** → **"Use Template"**
   - Select your template
   - Adjust date/time as needed

2. **Modify Template Data**
   - All template fields can be modified
   - Changes don't affect the original template
   - Save modifications as new templates

### Template Examples
```
Template: "Weekly Lab Meeting"
- Resource: Conference Room A
- Duration: 1 hour
- Title: "Lab Meeting - Week of {date}"
- Recurring: Weekly, Mondays at 10:00 AM
- Attendees: Research team members

Template: "PCR Standard Protocol"
- Resource: PCR Machine #1
- Duration: 3 hours
- Title: "PCR Analysis - {project}"
- Description: "Standard PCR protocol for {sample_type}"
- No attendees (individual work)

Template: "Equipment Training"
- Resource: [To be selected]
- Duration: 2 hours
- Title: "Training: {equipment} for {trainee}"
- Attendees: Trainer + Trainee
- Description: "Initial training session covering safety and operation"
```

## After Creating Your Booking

### Confirmation Process

#### Immediate Confirmation
For standard bookings:
- ✅ **Booking Confirmed**: Ready to use
- 📧 **Email Sent**: Confirmation with details
- 📅 **Calendar Added**: Appears on your calendar

#### Approval Required
For restricted resources:
- ⏳ **Pending Approval**: Waiting for administrator review
- 📧 **Notification Sent**: Approver receives request
- 🔔 **Status Updates**: You'll be notified of approval/rejection

### Managing Your Bookings

#### View Your Bookings
- **Dashboard**: Quick overview of upcoming bookings
- **My Bookings**: Complete list with filters
- **Calendar View**: Visual timeline of all bookings

#### Modify Bookings
- **Edit**: Change time, duration, or details
- **Duplicate**: Create similar bookings quickly
- **Cancel**: Remove bookings you no longer need
- **Extend**: Request additional time

#### Check-In and Check-Out
- **Check-In**: Confirm you're using the resource
- **Check-Out**: Mark when you've finished
- **Usage Tracking**: Helps improve scheduling accuracy

## Tips for Successful Bookings

### Planning Ahead
- 📅 **Book Early**: Popular resources fill up quickly
- ⏰ **Include Setup Time**: Factor in preparation and cleanup
- 🔄 **Use Recurring Bookings**: For regular activities
- 📋 **Create Templates**: For repeated booking types

### Optimizing Availability
- 🌅 **Consider Off-Peak Times**: Early morning or late day slots
- 📊 **Check Usage Patterns**: Avoid known busy periods
- 🔄 **Be Flexible**: Use waiting lists and alternative times
- 👥 **Coordinate with Team**: Share resources efficiently

### Being a Good Resource Citizen
- ✅ **Show Up on Time**: Respect other users' schedules
- 🚫 **Cancel Unused Bookings**: Free up time for others
- 📝 **Provide Accurate Descriptions**: Help others understand usage
- 🧹 **Clean Up After Use**: Leave resources ready for the next user

### Avoiding Common Mistakes
- ❌ **Don't book "just in case"** - only book what you'll use
- ❌ **Don't ignore training requirements** - complete them first
- ❌ **Don't book outside your expertise** - request training if needed
- ❌ **Don't modify others' bookings** - unless explicitly permitted

## Troubleshooting Common Issues

### "Resource not available"
- **Check prerequisites**: Training or approval required?
- **Verify permissions**: Do you have access to this resource?
- **Check operating hours**: Is the resource available at this time?
- **Contact administrator**: May need special access

### "Booking conflicts detected"
- **Review conflict details**: Understand what's overlapping
- **Use suggested alternatives**: System provides options
- **Join waiting list**: Get notified if time becomes available
- **Split the booking**: Create multiple shorter sessions

### "Form won't submit"
- **Check required fields**: All mandatory information filled?
- **Verify times**: Start time before end time?
- **Check duration limits**: Within resource's allowed range?
- **Clear browser cache**: Sometimes fixes form issues

### "Can't find resource"
- **Use search function**: Type resource name or keywords
- **Check filters**: Clear location or type filters
- **Browse categories**: Navigate through resource types
- **Contact administrator**: Resource may need to be added

## Advanced Features

### Keyboard Shortcuts
Speed up booking creation with shortcuts:
- `N`: New booking
- `T`: Use template
- `D`: Duplicate selected booking
- `E`: Edit selected booking
- `C`: Copy booking details

### Mobile Booking
Create bookings on your phone or tablet:
- **Responsive design**: Works on all devices
- **Touch-friendly**: Easy to use on touchscreens
- **Offline capability**: Basic functionality without internet
- **Quick booking**: Streamlined mobile interface

### Integration Features
Connect with your existing tools:
- **Calendar sync**: Export to Outlook, Google Calendar
- **Email notifications**: Customizable alert preferences
- **API access**: Programmatic booking creation
- **Webhook notifications**: Real-time updates to external systems

---

**You're now ready to create bookings like a pro!** The booking system is designed to be flexible and user-friendly while ensuring fair access to resources for everyone.

*Next: [Managing Your Bookings](managing-bookings.md) to learn about editing, canceling, and tracking your reservations*
# API Authentication Guide

Complete guide to authenticating with the Aperture Booking API, including token management, security best practices, and troubleshooting.

## Authentication Overview

Aperture Booking uses **token-based authentication** for API access. This provides secure, stateless authentication that's ideal for automated systems and integrations.

### Authentication Methods
- **Primary**: Token-based authentication (recommended)
- **Alternative**: Session-based authentication (for web applications)
- **Future**: OAuth 2.0 support (planned for enterprise deployments)

### Security Features
- **Secure Token Generation**: Cryptographically secure random tokens
- **Token Expiration**: Configurable token lifetime (default: 90 days)
- **Permission Scoping**: Tokens inherit user's role-based permissions
- **Audit Logging**: Complete audit trail of API access

## Obtaining API Tokens

### Method 1: Web Interface (Recommended)

#### For End Users
1. **Login to Aperture Booking**
   - Navigate to your institution's Aperture Booking URL
   - Login with your username and password

2. **Access API Settings**
   - Click your profile name in the top-right corner
   - Select **"Profile"** from the dropdown
   - Click on the **"API Access"** tab

3. **Generate Token**
   - Click **"Generate New API Token"**
   - Provide a descriptive name (e.g., "Lab Automation Script")
   - Optionally set expiration date
   - Click **"Create Token"**

4. **Secure Your Token**
   - **Copy the token immediately** - it's only shown once
   - Store in a secure location (password manager, environment variables)
   - Never share tokens or commit them to version control

#### Token Management Interface
```
API Token Management:
┌─────────────────────────────────────────────────┐
│ Token Name: Lab Automation Script               │
│ Created: 2025-01-20 14:30:00                   │
│ Last Used: 2025-01-20 16:45:00                 │
│ Expires: 2025-04-20 14:30:00                   │
│ Status: Active                                  │
│ Permissions: Standard User                      │
│ [Regenerate] [Revoke] [View Usage]             │
└─────────────────────────────────────────────────┘
```

### Method 2: Command Line (Administrators)

#### Using Django Management Command
```bash
# Create token for specific user
python manage.py create_api_token username@institution.edu

# Create token with custom expiration
python manage.py create_api_token username@institution.edu --expires-days 30

# Create token with description
python manage.py create_api_token username@institution.edu --description "Backup System Integration"

# List all tokens for user
python manage.py list_api_tokens username@institution.edu
```

#### Programmatic Token Creation
```python
# Django shell or management command
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

user = User.objects.get(username='username@institution.edu')
token, created = Token.objects.get_or_create(user=user)
print(f"Token: {token.key}")
```

### Method 3: API Endpoint (Advanced)

#### Authentication Token Endpoint
```http
POST /api/v1/auth/token/
Content-Type: application/json

{
  "username": "username@institution.edu",
  "password": "your-password"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b",
    "user_id": 123,
    "expires": "2025-04-20T14:30:00Z"
  },
  "message": "Authentication successful"
}
```

## Using API Tokens

### HTTP Header Authentication

#### Standard Usage
```http
GET /api/v1/resources/
Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b
Content-Type: application/json
```

#### Common HTTP Clients

##### cURL
```bash
curl -H "Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b" \
     -H "Content-Type: application/json" \
     https://your-institution.edu/api/v1/resources/
```

##### Python Requests
```python
import requests

headers = {
    'Authorization': 'Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b',
    'Content-Type': 'application/json'
}

response = requests.get(
    'https://your-institution.edu/api/v1/resources/',
    headers=headers
)

if response.status_code == 200:
    data = response.json()
    print("Success:", data)
else:
    print("Error:", response.status_code, response.text)
```

##### JavaScript/Node.js
```javascript
const fetch = require('node-fetch');

const headers = {
    'Authorization': 'Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b',
    'Content-Type': 'application/json'
};

fetch('https://your-institution.edu/api/v1/resources/', {
    method: 'GET',
    headers: headers
})
.then(response => response.json())
.then(data => console.log('Success:', data))
.catch(error => console.error('Error:', error));
```

##### PHP
```php
<?php
$headers = [
    'Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b',
    'Content-Type: application/json'
];

$context = stream_context_create([
    'http' => [
        'method' => 'GET',
        'header' => implode("\r\n", $headers)
    ]
]);

$response = file_get_contents(
    'https://your-institution.edu/api/v1/resources/',
    false,
    $context
);

$data = json_decode($response, true);
print_r($data);
?>
```

### SDK Authentication

#### Python SDK
```python
from aperture_booking import ApertureBookingClient

# Initialize client with token
client = ApertureBookingClient(
    base_url='https://your-institution.edu',
    token='9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b'
)

# Alternative: use environment variable
import os
client = ApertureBookingClient(
    base_url='https://your-institution.edu',
    token=os.environ['APERTURE_TOKEN']
)

# Make authenticated requests
resources = client.resources.list()
bookings = client.bookings.create(
    resource_id=15,
    title="Automated Booking",
    start_time="2025-01-21T09:00:00Z",
    end_time="2025-01-21T11:00:00Z"
)
```

#### JavaScript SDK
```javascript
import { ApertureBookingClient } from 'aperture-booking-sdk';

const client = new ApertureBookingClient({
    baseURL: 'https://your-institution.edu',
    token: process.env.APERTURE_TOKEN
});

// Make authenticated requests
const resources = await client.resources.list();
const booking = await client.bookings.create({
    resource_id: 15,
    title: "Automated Booking",
    start_time: "2025-01-21T09:00:00Z",
    end_time: "2025-01-21T11:00:00Z"
});
```

## Permission System

### Role-Based Access Control

API tokens inherit the permissions of the associated user account:

#### User Roles and API Permissions
```
Student:
- GET: Own bookings, public resources, calendar data
- POST: Create bookings (subject to approval rules)
- PUT: Edit own bookings
- DELETE: Cancel own bookings

Academic/Researcher:
- All Student permissions
- GET: Group bookings, extended resource details
- POST: Group bookings, booking templates
- PUT: Group booking management
- DELETE: Group booking cancellation

Lab Technician:
- All Academic permissions
- GET: All bookings for managed resources
- POST: Maintenance schedules, resource modifications
- PUT: Resource status updates, booking approvals
- DELETE: Emergency booking cancellations

Administrator:
- Full API access
- GET: All system data and analytics
- POST: User creation, system configuration
- PUT: All resource and user modifications
- DELETE: System-wide data management
```

### Scope-Limited Tokens (Enterprise Feature)

#### Creating Scoped Tokens
```python
# Create read-only token
token = create_scoped_token(
    user=user,
    scopes=['read:bookings', 'read:resources'],
    description='Read-only integration'
)

# Create resource-specific token
token = create_scoped_token(
    user=user,
    scopes=['read:resources', 'write:bookings'],
    resource_ids=[15, 16, 17],
    description='Lab A automation'
)
```

#### Available Scopes
```
Resource Scopes:
- read:resources - View resource information
- write:resources - Modify resource configuration
- admin:resources - Full resource management

Booking Scopes:
- read:bookings - View booking information
- write:bookings - Create and modify bookings
- admin:bookings - Administrative booking management

User Scopes:
- read:users - View user profiles
- write:users - Modify user information
- admin:users - User management and creation

System Scopes:
- read:analytics - Access system analytics
- write:maintenance - Schedule maintenance
- admin:system - Full system administration
```

## Token Security

### Security Best Practices

#### Token Storage
```bash
# Environment Variables (Recommended)
export APERTURE_TOKEN="9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"

# Configuration Files (Secure)
# ~/.aperture/config
[default]
token = 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b
base_url = https://your-institution.edu

# Docker Secrets
docker run -e APERTURE_TOKEN_FILE=/run/secrets/aperture_token myapp

# Kubernetes Secrets
apiVersion: v1
kind: Secret
metadata:
  name: aperture-token
data:
  token: OTk0NGIwOTE5OWM2MmJjZjk0MThhZDg0NmRkMGU0YmJkZmM2ZWU0Yg==
```

#### Security Guidelines
```
✅ DO:
- Store tokens in environment variables
- Use secure key management systems
- Rotate tokens regularly (every 90 days)
- Use separate tokens for different applications
- Monitor token usage for anomalies
- Revoke unused or compromised tokens immediately

❌ DON'T:
- Hardcode tokens in source code
- Commit tokens to version control
- Share tokens between users or applications
- Store tokens in plain text files
- Log tokens in application logs
- Use the same token across environments
```

### Token Rotation

#### Automatic Rotation (Recommended)
```python
# Automated token rotation script
import os
import requests
from datetime import datetime, timedelta

def rotate_token_if_needed():
    current_token = os.environ['APERTURE_TOKEN']
    
    # Check token expiration
    response = requests.get(
        'https://your-institution.edu/api/v1/auth/token/status/',
        headers={'Authorization': f'Token {current_token}'}
    )
    
    if response.status_code == 200:
        data = response.json()
        expires = datetime.fromisoformat(data['expires'])
        
        # Rotate if expiring in 7 days
        if expires < datetime.now() + timedelta(days=7):
            new_token = generate_new_token()
            update_environment_token(new_token)
            revoke_old_token(current_token)
```

#### Manual Rotation Process
1. **Generate New Token**: Create replacement token via web interface
2. **Update Applications**: Deploy new token to all applications
3. **Test Functionality**: Verify all integrations work with new token
4. **Revoke Old Token**: Remove old token from system
5. **Update Documentation**: Record rotation in change logs

### Monitoring and Auditing

#### Token Usage Monitoring
```python
# Check token usage statistics
response = requests.get(
    'https://your-institution.edu/api/v1/auth/token/usage/',
    headers={'Authorization': f'Token {token}'}
)

usage_data = response.json()
print(f"Requests today: {usage_data['requests_today']}")
print(f"Last used: {usage_data['last_used']}")
print(f"Total requests: {usage_data['total_requests']}")
```

#### Audit Logging
```
API Access Logs:
2025-01-20 14:30:00 | Token: abc123... | User: lab.automation@uni.edu | GET /api/v1/resources/ | 200
2025-01-20 14:31:00 | Token: abc123... | User: lab.automation@uni.edu | POST /api/v1/bookings/ | 201
2025-01-20 14:32:00 | Token: def456... | User: backup.system@uni.edu | GET /api/v1/bookings/ | 200
```

## Error Handling

### Authentication Errors

#### Invalid Token
```http
HTTP/1.1 401 Unauthorized
Content-Type: application/json

{
  "success": false,
  "data": null,
  "message": "Invalid authentication token",
  "errors": {
    "authentication": ["Token is invalid or has been revoked"]
  }
}
```

**Solutions:**
- Verify token is correct and not truncated
- Check if token has been revoked
- Generate new token if needed

#### Expired Token
```http
HTTP/1.1 401 Unauthorized
Content-Type: application/json

{
  "success": false,
  "data": null,
  "message": "Authentication token has expired",
  "errors": {
    "authentication": ["Token expired on 2025-01-15T10:30:00Z"]
  }
}
```

**Solutions:**
- Generate new token via web interface
- Update application configuration with new token
- Implement automatic token rotation

#### Missing Token
```http
HTTP/1.1 401 Unauthorized
Content-Type: application/json

{
  "success": false,
  "data": null,
  "message": "Authentication credentials not provided",
  "errors": {
    "authentication": ["No authentication token provided"]
  }
}
```

**Solutions:**
- Include Authorization header in request
- Verify header format: `Authorization: Token <token>`
- Check for typos in header name

#### Insufficient Permissions
```http
HTTP/1.1 403 Forbidden
Content-Type: application/json

{
  "success": false,
  "data": null,
  "message": "Insufficient permissions for this operation",
  "errors": {
    "permissions": ["User does not have permission to modify this resource"]
  }
}
```

**Solutions:**
- Verify user role has required permissions
- Request elevated access from administrator
- Use different user account with appropriate permissions

### Rate Limiting Errors

#### Rate Limit Exceeded
```http
HTTP/1.1 429 Too Many Requests
Content-Type: application/json
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1642694400

{
  "success": false,
  "data": null,
  "message": "Rate limit exceeded",
  "errors": {
    "rate_limit": ["Request limit of 1000 per hour exceeded"]
  }
}
```

**Solutions:**
- Implement exponential backoff in client code
- Reduce request frequency
- Cache responses to minimize API calls
- Contact administrator for rate limit increase

## Integration Examples

### Booking Automation System

#### Complete Integration Example
```python
import os
import requests
import logging
from datetime import datetime, timedelta

class ApertureBookingAPI:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Token {token}',
            'Content-Type': 'application/json'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def authenticate(self):
        """Verify token is valid"""
        response = self.session.get(f'{self.base_url}/api/v1/user/profile/')
        if response.status_code == 200:
            user_info = response.json()
            logging.info(f"Authenticated as: {user_info['data']['email']}")
            return True
        else:
            logging.error(f"Authentication failed: {response.text}")
            return False
    
    def create_booking(self, resource_id, title, start_time, end_time, description=None):
        """Create a new booking"""
        booking_data = {
            'resource': resource_id,
            'title': title,
            'start_time': start_time,
            'end_time': end_time,
            'description': description or f"Automated booking created at {datetime.now()}"
        }
        
        response = self.session.post(
            f'{self.base_url}/api/v1/bookings/',
            json=booking_data
        )
        
        if response.status_code == 201:
            booking = response.json()
            logging.info(f"Booking created: {booking['data']['id']}")
            return booking['data']
        else:
            logging.error(f"Booking creation failed: {response.text}")
            return None
    
    def check_availability(self, resource_id, start_time, end_time):
        """Check if resource is available"""
        params = {
            'start': start_time,
            'end': end_time
        }
        
        response = self.session.get(
            f'{self.base_url}/api/v1/resources/{resource_id}/availability/',
            params=params
        )
        
        if response.status_code == 200:
            availability = response.json()
            return len(availability['data']['available_slots']) > 0
        else:
            logging.error(f"Availability check failed: {response.text}")
            return False

# Usage example
def main():
    # Initialize API client
    api = ApertureBookingAPI(
        base_url='https://your-institution.edu',
        token=os.environ['APERTURE_TOKEN']
    )
    
    # Authenticate
    if not api.authenticate():
        return
    
    # Schedule tomorrow's analysis
    tomorrow = datetime.now() + timedelta(days=1)
    start_time = tomorrow.replace(hour=9, minute=0, second=0, microsecond=0)
    end_time = start_time + timedelta(hours=2)
    
    resource_id = 15  # PCR Machine #1
    
    # Check availability
    if api.check_availability(resource_id, start_time.isoformat(), end_time.isoformat()):
        # Create booking
        booking = api.create_booking(
            resource_id=resource_id,
            title="Automated PCR Analysis",
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
            description="Daily automated sample processing"
        )
        
        if booking:
            print(f"Successfully booked {booking['resource']['name']} for {start_time}")
        else:
            print("Failed to create booking")
    else:
        print("Resource not available at requested time")

if __name__ == "__main__":
    main()
```

### Calendar Synchronization

#### Two-Way Sync Implementation
```python
import icalendar
from datetime import datetime, timezone

class CalendarSync:
    def __init__(self, api_client):
        self.api = api_client
    
    def export_to_ical(self, start_date, end_date):
        """Export bookings to iCalendar format"""
        cal = icalendar.Calendar()
        cal.add('prodid', '-//Aperture Booking Integration//Calendar Sync//EN')
        cal.add('version', '2.0')
        
        # Get bookings from API
        params = {
            'start_time__gte': start_date.isoformat(),
            'start_time__lt': end_date.isoformat()
        }
        
        response = self.api.session.get(
            f'{self.api.base_url}/api/v1/bookings/',
            params=params
        )
        
        if response.status_code == 200:
            bookings = response.json()['data']['results']
            
            for booking in bookings:
                event = icalendar.Event()
                event.add('uid', f"booking-{booking['id']}@aperture-booking")
                event.add('summary', booking['title'])
                event.add('dtstart', datetime.fromisoformat(booking['start_time']))
                event.add('dtend', datetime.fromisoformat(booking['end_time']))
                event.add('description', booking.get('description', ''))
                event.add('location', booking['resource']['location'])
                
                cal.add_component(event)
        
        return cal.to_ical()
    
    def sync_external_calendar(self, external_events):
        """Create bookings from external calendar events"""
        for event in external_events:
            # Check if booking already exists
            existing = self.find_existing_booking(event.get('uid'))
            
            if not existing:
                # Create new booking
                booking_data = {
                    'resource': self.map_location_to_resource(event.get('location')),
                    'title': str(event.get('summary')),
                    'start_time': event.get('dtstart').dt.isoformat(),
                    'end_time': event.get('dtend').dt.isoformat(),
                    'description': f"Imported from external calendar: {event.get('description', '')}"
                }
                
                self.api.create_booking(**booking_data)
```

## Testing and Development

### Testing Authentication

#### Unit Tests
```python
import unittest
from unittest.mock import patch, Mock

class TestAPIAuthentication(unittest.TestCase):
    def setUp(self):
        self.base_url = 'https://test.aperture-booking.edu'
        self.token = 'test-token-123456789'
        self.api = ApertureBookingAPI(self.base_url, self.token)
    
    @patch('requests.Session.get')
    def test_valid_authentication(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': {'email': 'test@example.com'}
        }
        mock_get.return_value = mock_response
        
        result = self.api.authenticate()
        
        self.assertTrue(result)
        mock_get.assert_called_once_with(f'{self.base_url}/api/v1/user/profile/')
    
    @patch('requests.Session.get')
    def test_invalid_authentication(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = 'Invalid token'
        mock_get.return_value = mock_response
        
        result = self.api.authenticate()
        
        self.assertFalse(result)
```

#### Integration Tests
```python
import os
import pytest
from datetime import datetime, timedelta

@pytest.fixture
def api_client():
    return ApertureBookingAPI(
        base_url=os.environ.get('TEST_BASE_URL', 'https://sandbox.aperture-booking.edu'),
        token=os.environ.get('TEST_TOKEN')
    )

def test_authentication_integration(api_client):
    """Test authentication with real API"""
    assert api_client.authenticate(), "Authentication should succeed with valid token"

def test_booking_creation_integration(api_client):
    """Test booking creation with real API"""
    # Use sandbox resource for testing
    resource_id = 1
    tomorrow = datetime.now() + timedelta(days=1)
    start_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
    end_time = start_time + timedelta(hours=1)
    
    booking = api_client.create_booking(
        resource_id=resource_id,
        title="Integration Test Booking",
        start_time=start_time.isoformat(),
        end_time=end_time.isoformat()
    )
    
    assert booking is not None, "Booking creation should succeed"
    assert booking['title'] == "Integration Test Booking"
```

### Sandbox Environment

#### Test Environment Setup
```bash
# Set up test environment variables
export TEST_BASE_URL="https://sandbox.aperture-booking.edu"
export TEST_TOKEN="sandbox-token-for-testing"

# Run integration tests
python -m pytest tests/integration/ -v

# Load test data
python manage.py loaddata sandbox_data.json
```

#### Sandbox Features
- **Reset Daily**: All data resets at midnight UTC
- **Test Resources**: Pre-configured resources for testing
- **Sample Users**: Test accounts with different permission levels
- **Mock Data**: Realistic but safe test data
- **Rate Limits**: Relaxed rate limits for development

---

**Secure API authentication is the foundation of reliable integrations.** Follow these guidelines to ensure your applications can safely and effectively interact with the Aperture Booking API.

*Next: [API Endpoints Reference](endpoints.md) for detailed information about available API endpoints and their usage*
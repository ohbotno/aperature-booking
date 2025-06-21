# API Overview

Aperture Booking provides a comprehensive REST API for integrating with external systems, building custom applications, and automating booking workflows.

## API Fundamentals

### Base URL
```
https://your-institution.edu/api/v1/
```

### Authentication
The API uses token-based authentication:

```http
Authorization: Token your-api-token-here
```

### Content Type
All API requests should use JSON:

```http
Content-Type: application/json
```

### Response Format
All responses are in JSON format with consistent structure:

```json
{
  "success": true,
  "data": {...},
  "message": "Operation completed successfully",
  "errors": null
}
```

## Getting Started

### 1. Obtain API Token

#### For Users
1. Login to Aperture Booking
2. Go to **Profile > API Access**
3. Click **"Generate API Token"**
4. Copy and securely store your token

#### For Administrators
```bash
# Django management command
python manage.py create_api_token username
```

### 2. Make Your First Request

```bash
curl -H "Authorization: Token your-token" \
     -H "Content-Type: application/json" \
     https://your-institution.edu/api/v1/user/profile/
```

### 3. Handle Responses

```python
import requests

headers = {
    'Authorization': 'Token your-token',
    'Content-Type': 'application/json'
}

response = requests.get(
    'https://your-institution.edu/api/v1/resources/',
    headers=headers
)

if response.status_code == 200:
    data = response.json()
    resources = data['data']['results']
else:
    print(f"Error: {response.status_code}")
```

## Core API Endpoints

### Authentication & Users

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth/login/` | POST | Authenticate and get token |
| `/auth/logout/` | POST | Invalidate current token |
| `/user/profile/` | GET, PUT | Get/update user profile |
| `/user/preferences/` | GET, PUT | Manage user preferences |

### Resources

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/resources/` | GET | List all available resources |
| `/resources/{id}/` | GET | Get resource details |
| `/resources/{id}/availability/` | GET | Check resource availability |
| `/resources/{id}/access-request/` | POST | Request access to resource |

### Bookings

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/bookings/` | GET, POST | List/create bookings |
| `/bookings/{id}/` | GET, PUT, DELETE | Manage specific booking |
| `/bookings/{id}/check-in/` | POST | Check in to booking |
| `/bookings/{id}/check-out/` | POST | Check out of booking |
| `/bookings/conflicts/` | GET | Check for booking conflicts |

### Calendar & Scheduling

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/calendar/events/` | GET | Get calendar events |
| `/calendar/availability/` | GET | Check time slot availability |
| `/calendar/export/` | GET | Export calendar data |
| `/recurring-bookings/` | GET, POST | Manage recurring bookings |

### Maintenance

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/maintenance/` | GET, POST | List/schedule maintenance |
| `/maintenance/{id}/` | GET, PUT | Manage maintenance records |
| `/maintenance/alerts/` | GET | Get maintenance alerts |
| `/maintenance/analytics/` | GET | Maintenance analytics data |

### Notifications

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/notifications/` | GET | List user notifications |
| `/notifications/{id}/read/` | POST | Mark notification as read |
| `/notifications/preferences/` | GET, PUT | Notification settings |
| `/notifications/send/` | POST | Send custom notification |

## Request/Response Examples

### Create a Booking

**Request:**
```http
POST /api/v1/bookings/
Authorization: Token your-token
Content-Type: application/json

{
  "resource": 15,
  "title": "PCR Analysis",
  "start_time": "2025-01-20T09:00:00Z",
  "end_time": "2025-01-20T11:00:00Z",
  "description": "Running PCR samples for project X",
  "attendees": [
    {"user": 25, "role": "participant"}
  ]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 123,
    "resource": {
      "id": 15,
      "name": "PCR Machine #1",
      "location": "Lab A-101"
    },
    "title": "PCR Analysis",
    "start_time": "2025-01-20T09:00:00Z",
    "end_time": "2025-01-20T11:00:00Z",
    "status": "confirmed",
    "created_at": "2025-01-18T14:30:00Z"
  },
  "message": "Booking created successfully"
}
```

### Check Resource Availability

**Request:**
```http
GET /api/v1/resources/15/availability/?start=2025-01-20T00:00:00Z&end=2025-01-27T00:00:00Z
Authorization: Token your-token
```

**Response:**
```json
{
  "success": true,
  "data": {
    "resource_id": 15,
    "available_slots": [
      {
        "start": "2025-01-20T08:00:00Z",
        "end": "2025-01-20T09:00:00Z"
      },
      {
        "start": "2025-01-20T11:00:00Z",
        "end": "2025-01-20T17:00:00Z"
      }
    ],
    "booked_slots": [
      {
        "start": "2025-01-20T09:00:00Z",
        "end": "2025-01-20T11:00:00Z",
        "booking_id": 123,
        "title": "PCR Analysis"
      }
    ],
    "maintenance_slots": []
  }
}
```

## Pagination

Large result sets are paginated:

```json
{
  "success": true,
  "data": {
    "count": 150,
    "next": "https://api.example.com/bookings/?page=2",
    "previous": null,
    "results": [...]
  }
}
```

**Query Parameters:**
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 20, max: 100)

## Filtering and Searching

### Common Filters

**Bookings:**
```
GET /bookings/?status=confirmed&resource=15&start_date=2025-01-20
```

**Resources:**
```
GET /resources/?resource_type=equipment&location=Lab%20A&available=true
```

**Search:**
```
GET /resources/?search=PCR
GET /bookings/?search=project%20X
```

### Date Filtering
```
GET /bookings/?start_time__gte=2025-01-20T00:00:00Z&start_time__lt=2025-01-21T00:00:00Z
```

## Error Handling

### HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 409 | Conflict |
| 429 | Rate Limited |
| 500 | Server Error |

### Error Response Format

```json
{
  "success": false,
  "data": null,
  "message": "Validation failed",
  "errors": {
    "start_time": ["This field is required."],
    "resource": ["Resource not available at this time."]
  }
}
```

## Rate Limiting

- **Default limit**: 1000 requests per hour per token
- **Burst limit**: 60 requests per minute per token
- **Headers included** in responses:
  - `X-RateLimit-Limit`: Rate limit ceiling
  - `X-RateLimit-Remaining`: Requests remaining
  - `X-RateLimit-Reset`: Time when limit resets

## Webhooks

Subscribe to real-time events:

### Supported Events
- `booking.created`
- `booking.modified`
- `booking.cancelled`
- `maintenance.scheduled`
- `access_request.submitted`
- `approval.required`

### Webhook Configuration
```http
POST /api/v1/webhooks/
{
  "url": "https://your-app.com/webhook",
  "events": ["booking.created", "booking.cancelled"],
  "secret": "your-webhook-secret"
}
```

## SDK and Libraries

### Official SDKs
- **Python**: `pip install aperture-booking-sdk`
- **JavaScript**: `npm install aperture-booking-sdk`
- **PHP**: `composer require aperture/booking-sdk`

### Community Libraries
- **R**: Available on CRAN
- **MATLAB**: File Exchange
- **LabVIEW**: Toolkit available

## Common Integration Patterns

### 1. Calendar Synchronization
```python
# Sync bookings to external calendar
bookings = api.get_bookings(start_date=today)
for booking in bookings:
    calendar.create_event(booking.to_calendar_event())
```

### 2. Automated Booking
```python
# Book based on external triggers
def book_instrument_after_prep():
    if prep_complete():
        api.create_booking(
            resource_id=15,
            title="Automated Analysis",
            start_time=datetime.now() + timedelta(minutes=30),
            duration=timedelta(hours=2)
        )
```

### 3. Usage Analytics
```python
# Generate custom reports
usage_data = api.get_analytics(
    resource_ids=[15, 16, 17],
    start_date="2025-01-01",
    end_date="2025-01-31"
)
report = generate_utilization_report(usage_data)
```

## Best Practices

### 1. Token Security
- Store tokens securely (environment variables, key vaults)
- Rotate tokens regularly
- Use separate tokens for different applications

### 2. Error Handling
- Always check response status codes
- Implement retry logic for transient errors
- Log errors for debugging

### 3. Performance
- Use pagination for large datasets
- Cache frequently accessed data
- Implement request timeouts

### 4. Rate Limiting
- Respect rate limits
- Implement exponential backoff
- Use webhooks instead of polling when possible

## Testing

### Sandbox Environment
- **URL**: `https://sandbox.aperture-booking.edu/api/v1/`
- **Test data**: Pre-populated with sample resources and bookings
- **Reset**: Data resets daily at midnight UTC

### API Testing Tools
- **Postman Collection**: Available for download
- **OpenAPI Spec**: Swagger/OpenAPI 3.0 specification
- **curl Examples**: Command-line examples for all endpoints

## Support and Resources

### Documentation
- **Interactive API Docs**: `/api/docs/` (Swagger UI)
- **Schema**: `/api/schema/` (OpenAPI specification)
- **Changelog**: Track API changes and updates

### Getting Help
- **Developer Forum**: Community support and discussions
- **Email Support**: api-support@aperture-booking.org
- **Status Page**: Monitor API availability and incidents

### Contributing
- **GitHub**: Submit issues and feature requests
- **SDK Development**: Contribute to official SDKs
- **Documentation**: Help improve API documentation

---

**Ready to start building?** Check out our [endpoint reference](endpoints.md) and [integration examples](examples.md) to begin developing with the Aperture Booking API.

*Next: [Authentication Guide](authentication.md) for detailed authentication setup*
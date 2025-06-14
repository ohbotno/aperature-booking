# How to Test - Lab Booking System

This guide explains how to run tests for the Lab Booking System.

## Prerequisites

1. **Activate the virtual environment**
   ```bash
   cd "/path/to/aperture_booking"
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install test dependencies** (if not already installed)
   ```bash
   pip install pytest pytest-django pytest-cov factory-boy
   ```

## Running Tests

### Basic Test Execution

```bash
# Run all tests with verbose output
python -m pytest booking/tests/ -v

# Run tests with coverage report
python -m pytest booking/tests/ --cov=booking --cov-report=term-missing

# Generate HTML coverage report
python -m pytest booking/tests/ --cov=booking --cov-report=html
```

### Specific Test Execution

```bash
# Run specific test file
python -m pytest booking/tests/test_models.py -v

# Run specific test class
python -m pytest booking/tests/test_models.py::TestBooking -v

# Run specific test method
python -m pytest booking/tests/test_models.py::TestBooking::test_booking_creation -v
```

### Alternative: Django Test Runner

```bash
# Run all booking tests
python manage.py test booking.tests

# Run specific test module
python manage.py test booking.tests.test_models

# Run with verbosity
python manage.py test booking.tests -v 2
```

## Test Organization

The test suite is organized into several modules:

### Core Test Files
- **`test_models.py`** - Model validation, business logic, relationships
- **`test_api.py`** - REST API endpoints, authentication, permissions
- **`test_conflicts.py`** - Booking conflict detection and resolution
- **`test_basic.py`** - Basic Django setup and configuration
- **`factories.py`** - Test data factories for consistent test objects

### Test Categories
Tests are marked with pytest markers:
- `@pytest.mark.django_db` - Tests requiring database access
- `@pytest.mark.slow` - Long-running tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.unit` - Unit tests

## Test Coverage

The project is configured for 80% minimum test coverage. Coverage reports show:
- Line coverage percentages
- Missing lines that need test coverage
- HTML reports for detailed analysis

### View Coverage Report
After running tests with coverage:
```bash
# Open HTML report (generated in htmlcov/ directory)
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

## Testing Best Practices

### Using Factories
The test suite uses Factory Boy for creating test data:
```python
# Create test objects with realistic data
user = UserProfileFactory()
resource = ResourceFactory()
booking = BookingFactory(user=user, resource=resource)
```

### Database Isolation
Each test runs in an isolated database transaction:
```python
@pytest.mark.django_db
class TestBooking:
    def test_booking_creation(self):
        # Database changes are rolled back after each test
        booking = BookingFactory()
        assert booking.status == 'pending'
```

### API Testing
API tests use Django REST Framework's test client:
```python
def setup_method(self):
    self.client = APIClient()
    self.user = UserProfileFactory()
    self.client.force_authenticate(user=self.user.user)
```

## Current Test Coverage

The existing test suite covers:

### ✅ Model Tests
- User profile creation and validation
- Resource access control and training requirements
- Booking conflict detection and validation
- Approval rule logic and application
- Template usage and management

### ✅ API Tests
- CRUD operations for all major models
- Authentication and authorization
- Role-based permissions
- Calendar event formatting
- Bulk operations (approve/reject)
- Statistics endpoints

### ✅ Conflict Resolution
- Time-based conflicts
- Resource capacity limits
- Maintenance window blocking
- Alternative time/resource suggestions
- Priority-based resolution

### ✅ Integration Tests
- Calendar API integration
- User authentication flows
- Cross-model relationships
- Bulk operations

## Troubleshooting

### Common Issues

1. **"No module named 'booking'"**
   - Ensure you're in the correct directory with `manage.py`
   - Check that Django can find the booking app

2. **Database errors**
   - Run migrations: `python manage.py migrate`
   - Check database configuration in settings

3. **Import errors**
   - Verify all test dependencies are installed
   - Check Python path and virtual environment

4. **Permission errors**
   - Ensure test database can be created/modified
   - Check file permissions for SQLite database

### Debug Mode
Run tests with additional debugging:
```bash
# More verbose output
python -m pytest booking/tests/ -vv

# Stop on first failure
python -m pytest booking/tests/ -x

# Drop into debugger on failures
python -m pytest booking/tests/ --pdb

# Show print statements
python -m pytest booking/tests/ -s
```

## Adding New Tests

When adding features, follow these patterns:

1. **Add factories** for new models in `factories.py`
2. **Write model tests** for business logic validation
3. **Add API tests** for new endpoints
4. **Include integration tests** for complex workflows
5. **Update coverage** to maintain 80% minimum

### Example Test Structure
```python
@pytest.mark.django_db
class TestNewFeature:
    def setup_method(self):
        """Set up test data for each test method."""
        self.user = UserProfileFactory()
    
    def test_feature_creation(self):
        """Test basic feature functionality."""
        # Arrange
        # Act
        # Assert
        pass
    
    def test_feature_validation(self):
        """Test feature validation rules."""
        pass
    
    def test_feature_permissions(self):
        """Test feature access control."""
        pass
```

---

**Note**: This test suite provides comprehensive coverage of the Lab Booking System's core functionality. Regular test execution ensures code quality and prevents regressions during development.
# Risk Assessment Implementation - TODO

## Current Status
The risk assessment logic has been implemented but the database field is temporarily disabled due to missing dependencies.

## What's Working Now
- Risk assessment priority logic: Training → Risk Assessment → Request Access
- Risk assessments are checked based on existing RiskAssessment records with `is_mandatory=True`
- The `requires_risk_assessment_safe` property checks for mandatory risk assessments
- Button display logic correctly prioritizes training completion before risk assessment

## To Complete Implementation

### 1. Install Missing Dependencies
```bash
pip install django-apscheduler
```

### 2. Update the Resource Model
Uncomment the field in `/booking/models.py` (lines 748-753):
```python
requires_risk_assessment = models.BooleanField(
    default=False,
    null=True,
    blank=True,
    help_text="Require users to complete a risk assessment before accessing this resource"
)
```

### 3. Update the Migration
Uncomment the operations in `/booking/migrations/0009_add_requires_risk_assessment_field.py`

### 4. Run the Migration
```bash
python manage.py migrate booking
```

### 5. Update the ResourceForm
Add `'requires_risk_assessment'` back to the fields list in `/booking/forms.py` (around line 1231)

### 6. Update the Form Template
Re-add the checkbox section to `/booking/templates/booking/lab_admin_resource_form.html` (after line 210):
```html
<div class="mb-3">
    <div class="form-check">
        {{ form.requires_risk_assessment }}
        <label class="form-check-label" for="{{ form.requires_risk_assessment.id_for_label }}">
            {{ form.requires_risk_assessment.label }}
        </label>
    </div>
    {% if form.requires_risk_assessment.help_text %}
    <small class="form-text text-muted">{{ form.requires_risk_assessment.help_text }}</small>
    {% endif %}
    {% if form.requires_risk_assessment.errors %}
    <div class="text-danger">
        {% for error in form.requires_risk_assessment.errors %}
        <small>{{ error }}</small>
        {% endfor %}
    </div>
    {% endif %}
</div>
```

### 7. Update the Property (Optional)
Once the field exists, you can simplify the `requires_risk_assessment_safe` property to just return the field value:
```python
@property
def requires_risk_assessment_safe(self):
    return self.requires_risk_assessment
```

## Alternative: Manual Database Update
If you need to apply the change immediately without installing dependencies:
```sql
ALTER TABLE booking_resource ADD COLUMN requires_risk_assessment BOOLEAN DEFAULT 0;
```

## Current Workaround
The system currently determines if a resource requires risk assessment by checking if any mandatory risk assessments are assigned to it. This works but is less efficient than having a dedicated boolean field.
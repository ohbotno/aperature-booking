-- Manual SQL migration to add requires_risk_assessment field
-- Run this in your SQLite database if automatic migration fails

ALTER TABLE booking_resource ADD COLUMN requires_risk_assessment BOOLEAN DEFAULT 0;

-- Update the field to nullable
UPDATE booking_resource SET requires_risk_assessment = 0 WHERE requires_risk_assessment IS NULL;
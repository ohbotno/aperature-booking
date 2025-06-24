#!/bin/bash
"""
Gunicorn startup script for Aperture Booking.

This script starts Gunicorn with the appropriate settings for production.
"""

# Configuration
NAME="aperture-booking"
DJANGODIR="/opt/aperture-booking"
SOCKFILE="/var/run/aperture-booking/gunicorn.sock"
USER="aperture-booking"
GROUP="aperture-booking"
NUM_WORKERS=3
DJANGO_SETTINGS_MODULE="aperture_booking.settings_production"
DJANGO_WSGI_MODULE="aperture_booking.wsgi"

# Activate virtual environment
cd $DJANGODIR
source venv/bin/activate
export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE
export PYTHONPATH=$DJANGODIR:$PYTHONPATH

# Create run directory if it doesn't exist
RUNDIR=$(dirname $SOCKFILE)
test -d $RUNDIR || mkdir -p $RUNDIR

# Start Gunicorn
exec gunicorn ${DJANGO_WSGI_MODULE}:application \
  --name $NAME \
  --workers $NUM_WORKERS \
  --user=$USER --group=$GROUP \
  --bind=unix:$SOCKFILE \
  --log-level=info \
  --log-file=- \
  --timeout=120 \
  --graceful-timeout=30 \
  --max-requests=1000 \
  --max-requests-jitter=100 \
  --preload
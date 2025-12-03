#!/bin/bash
set -e

# Set the project directory
PROJECT_DIR="/home/team/ai-api/venv/samp/R4I-team6"
VENV_DIR="$PROJECT_DIR/venv"

cd "$PROJECT_DIR" || exit 1

if [ ! -d "$VENV_DIR" ]; then
    echo "Error: venv not found at $VENV_DIR"
    exit 1
fi

# Activate venv (optional if we use direct paths, but good for env vars)
source "$VENV_DIR/bin/activate"

export FLASK_APP=app.py
export FLASK_DEBUG=0

# Initialize/Upgrade Database using the venv python
"$VENV_DIR/bin/python" -m flask db upgrade

# Run with Gunicorn using the venv executable
# -w 4: 4 worker processes
# -b 0.0.0.0:5000: Bind to all interfaces on port 5000
# --access-logfile -: Log access to stdout
# --error-logfile -: Log errors to stderr
exec "$VENV_DIR/bin/gunicorn" -w 4 -b 0.0.0.0:5000 --access-logfile - --error-logfile - app:app
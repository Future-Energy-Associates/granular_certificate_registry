#!/bin/bash
set -e

# Print diagnostic information
echo "======================= STARTING CERTIFICATE ISSUANCE TASK ======================="
echo "Current date: $(date)"
echo "Working directory: $(pwd)"
echo "Current user: $(whoami)"

# Navigate to code directory
echo "======================= CHANGING TO CODE DIRECTORY ======================="
cd /code
echo "Working directory after cd: $(pwd)"
echo "Directory contents:"
ls -la

# Create log directory
echo "======================= SETTING UP LOG DIRECTORY ======================="
mkdir -p /code/logs
echo "Log directory created at /code/logs"

# Check for date parameters in environment variables
echo "======================= CHECKING PARAMETERS ======================="
FROM_DATE=${FROM_DATE:-""}
TO_DATE=${TO_DATE:-""}

DATE_PARAMS=""
if [ ! -z "$FROM_DATE" ]; then
  DATE_PARAMS="$DATE_PARAMS --from_date $FROM_DATE"
  echo "Using custom from_date: $FROM_DATE"
fi

if [ ! -z "$TO_DATE" ]; then
  DATE_PARAMS="$DATE_PARAMS --to_date $TO_DATE"
  echo "Using custom to_date: $TO_DATE"
fi

if [ -z "$DATE_PARAMS" ]; then
  echo "Using default date range (yesterday to today)"
fi

# Run the actual task
echo "======================= RUNNING CERTIFICATE ISSUANCE TASK ======================="
echo "Running with parameters: $DATE_PARAMS"
/usr/local/bin/poetry run python gc_registry/certificate/issuance_task.py $DATE_PARAMS

# Check exit code
EXIT_CODE=$?
echo "======================= TASK COMPLETED ======================="
echo "Exit code: $EXIT_CODE"

if [ $EXIT_CODE -ne 0 ]; then
  echo "Task failed with error code: $EXIT_CODE"
  exit $EXIT_CODE
fi

echo "Task completed successfully!"
echo "======================= END OF SCRIPT ======================="
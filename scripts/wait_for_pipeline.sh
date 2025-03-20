#!/bin/bash

# Script to wait for GitHub Actions pipelines to finish
# Usage: ./wait_for_pipeline.sh [timeout_seconds]

# Default timeout of 15 minutes if not specified
TIMEOUT=${1:-900}
SLEEP_INTERVAL=10
ELAPSED=0

# Function to check if all checks are complete
function checks_complete() {
  # Get the checks status - look for any pending or in_progress checks
  PENDING=$(gh pr checks 2>/dev/null | grep -E 'pending|in_progress')
  
  # If no pending checks, we're done
  if [ -z "$PENDING" ]; then
    return 0
  else
    return 1
  fi
}

echo "Waiting for GitHub Actions pipelines to complete (timeout: ${TIMEOUT}s)"
echo "Press Ctrl+C to stop waiting"

while ! checks_complete && [ $ELAPSED -lt $TIMEOUT ]; do
  # Print current status
  echo "Pipeline status at $(date +%H:%M:%S):"
  gh pr checks 2>/dev/null | column -t
  
  # Sleep before checking again
  sleep $SLEEP_INTERVAL
  ELAPSED=$((ELAPSED + SLEEP_INTERVAL))
  
  # Print a separator
  echo "------------------------------------------------------"
done

# Final status check
if checks_complete; then
  echo "All pipelines completed!"
  gh pr checks 2>/dev/null | column -t
  
  # Check if any checks failed
  FAILED=$(gh pr checks 2>/dev/null | grep -E 'fail')
  if [ -n "$FAILED" ]; then
    echo -e "\n❌ Some checks failed. See details above."
    exit 1
  else
    echo -e "\n✅ All checks passed successfully!"
    exit 0
  fi
else
  echo "Timeout reached. Some pipelines are still running:"
  gh pr checks 2>/dev/null | column -t
  exit 2
fi
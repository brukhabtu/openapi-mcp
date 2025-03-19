#!/bin/bash

# Advanced script to watch GitHub Actions CI runs
# Usage:
#   ./watch_ci.sh                     - Watch current PR checks
#   ./watch_ci.sh --run RUN_ID        - Watch specific run by ID
#   ./watch_ci.sh --workflow NAME     - Watch latest run of workflow NAME
#   ./watch_ci.sh --branch BRANCH     - Watch latest run on branch BRANCH
#   ./watch_ci.sh --timeout SECONDS   - Set timeout (default: 900s)

TIMEOUT=900
SLEEP_INTERVAL=10
ELAPSED=0
MODE="pr" # Default mode is to watch PR checks

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --run)
      RUN_ID="$2"
      MODE="run"
      shift 2
      ;;
    --workflow)
      WORKFLOW="$2"
      MODE="workflow"
      shift 2
      ;;
    --branch)
      BRANCH="$2"
      MODE="branch"
      shift 2
      ;;
    --timeout)
      TIMEOUT="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: ./watch_ci.sh [--run RUN_ID | --workflow NAME | --branch BRANCH] [--timeout SECONDS]"
      exit 1
      ;;
  esac
done

function get_run_status() {
  case $MODE in
    pr)
      gh pr checks 2>/dev/null
      ;;
    run)
      gh run view "$RUN_ID" --json status,name,conclusion,jobs | jq -r '.jobs[] | "\(.name)\t\(.status)\t\(.conclusion)"'
      ;;
    workflow)
      WORKFLOW_RUN=$(gh run list --workflow "$WORKFLOW" --limit 1 --json databaseId | jq -r '.[0].databaseId')
      if [ -n "$WORKFLOW_RUN" ]; then
        gh run view "$WORKFLOW_RUN" --json status,name,conclusion,jobs | jq -r '.jobs[] | "\(.name)\t\(.status)\t\(.conclusion)"'
      else
        echo "No runs found for workflow $WORKFLOW"
        return 1
      fi
      ;;
    branch)
      BRANCH_RUN=$(gh run list --branch "$BRANCH" --limit 1 --json databaseId | jq -r '.[0].databaseId')
      if [ -n "$BRANCH_RUN" ]; then
        gh run view "$BRANCH_RUN" --json status,name,conclusion,jobs | jq -r '.jobs[] | "\(.name)\t\(.status)\t\(.conclusion)"'
      else
        echo "No runs found for branch $BRANCH"
        return 1
      fi
      ;;
  esac
}

function is_complete() {
  case $MODE in
    pr)
      PENDING=$(gh pr checks 2>/dev/null | grep -E 'pending|in_progress')
      ;;
    run)
      PENDING=$(gh run view "$RUN_ID" --json status | jq -r '.status' | grep -E 'in_progress|queued|pending|waiting')
      ;;
    workflow)
      WORKFLOW_RUN=$(gh run list --workflow "$WORKFLOW" --limit 1 --json databaseId,status | jq -r '.[0]')
      PENDING=$(echo "$WORKFLOW_RUN" | jq -r '.status' | grep -E 'in_progress|queued|pending|waiting')
      ;;
    branch)
      BRANCH_RUN=$(gh run list --branch "$BRANCH" --limit 1 --json databaseId,status | jq -r '.[0]')
      PENDING=$(echo "$BRANCH_RUN" | jq -r '.status' | grep -E 'in_progress|queued|pending|waiting')
      ;;
  esac
  
  if [ -z "$PENDING" ]; then
    return 0
  else
    return 1
  fi
}

echo "Watching GitHub Actions CI (mode: $MODE, timeout: ${TIMEOUT}s)"
echo "Press Ctrl+C to stop watching"

while ! is_complete && [ $ELAPSED -lt $TIMEOUT ]; do
  echo "CI status at $(date +%H:%M:%S):"
  get_run_status | column -t
  
  sleep $SLEEP_INTERVAL
  ELAPSED=$((ELAPSED + SLEEP_INTERVAL))
  
  echo "------------------------------------------------------"
done

# Final status check
if is_complete; then
  echo "All CI jobs completed!"
  get_run_status | column -t
  
  # Check if any jobs failed
  FAILED=$(get_run_status | grep -E 'fail|cancelled|timed_out')
  if [ -n "$FAILED" ]; then
    echo -e "\n❌ Some jobs failed. See details above."
    exit 1
  else
    echo -e "\n✅ All jobs completed successfully!"
    exit 0
  fi
else
  echo "Timeout reached. Some jobs are still running:"
  get_run_status | column -t
  exit 2
fi
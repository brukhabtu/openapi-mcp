#!/bin/bash

# Script to display a visual summary of CI pipeline status
# Usage: ./ci_status.sh [--branch BRANCH | --pr PR_NUMBER]

BRANCH=""
PR_NUMBER=""

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --branch)
      BRANCH="$2"
      shift 2
      ;;
    --pr)
      PR_NUMBER="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: ./ci_status.sh [--branch BRANCH | --pr PR_NUMBER]"
      exit 1
      ;;
  esac
done

# ANSI color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Status symbols
SUCCESS="✅"
FAILURE="❌"
PENDING="🔄"
SKIPPED="⏭️"
UNKNOWN="❓"

# Get workflows and their status
get_workflows() {
  if [ -n "$BRANCH" ]; then
    gh run list --branch "$BRANCH" --limit 10 --json databaseId,name,status,conclusion,workflowName,headBranch,event
  elif [ -n "$PR_NUMBER" ]; then
    PR_BRANCH=$(gh pr view "$PR_NUMBER" --json headRefName -q .headRefName)
    gh run list --branch "$PR_BRANCH" --limit 10 --json databaseId,name,status,conclusion,workflowName,headBranch,event
  else
    # Use current branch if no specific branch or PR is provided
    CURRENT_BRANCH=$(git branch --show-current)
    gh run list --branch "$CURRENT_BRANCH" --limit 10 --json databaseId,name,status,conclusion,workflowName,headBranch,event
  fi
}

# Format the status with color and emoji
format_status() {
  local status=$1
  local conclusion=$2
  
  if [ "$status" == "completed" ]; then
    if [ "$conclusion" == "success" ]; then
      echo -e "${GREEN}${SUCCESS} Success${NC}"
    elif [ "$conclusion" == "failure" ]; then
      echo -e "${RED}${FAILURE} Failed${NC}"
    elif [ "$conclusion" == "skipped" ]; then
      echo -e "${BLUE}${SKIPPED} Skipped${NC}"
    else
      echo -e "${YELLOW}${UNKNOWN} ${conclusion}${NC}"
    fi
  elif [ "$status" == "in_progress" ]; then
    echo -e "${YELLOW}${PENDING} Running${NC}"
  elif [ "$status" == "queued" ]; then
    echo -e "${BLUE}${PENDING} Queued${NC}"
  else
    echo -e "${YELLOW}${UNKNOWN} ${status}${NC}"
  fi
}

# Main function to display workflow status
display_workflows() {
  echo -e "${BOLD}CI Pipeline Status Summary${NC}"
  echo "----------------------------------------"
  
  if [ -n "$BRANCH" ]; then
    echo -e "Branch: ${BOLD}$BRANCH${NC}"
  elif [ -n "$PR_NUMBER" ]; then
    PR_TITLE=$(gh pr view "$PR_NUMBER" --json title -q .title)
    PR_BRANCH=$(gh pr view "$PR_NUMBER" --json headRefName -q .headRefName)
    echo -e "PR #$PR_NUMBER: ${BOLD}$PR_TITLE${NC}"
    echo -e "Branch: ${BOLD}$PR_BRANCH${NC}"
  else
    CURRENT_BRANCH=$(git branch --show-current)
    echo -e "Current branch: ${BOLD}$CURRENT_BRANCH${NC}"
  fi
  
  echo "----------------------------------------"
  
  # Get workflows and display them
  WORKFLOWS=$(get_workflows)
  
  if [ -z "$WORKFLOWS" ]; then
    echo -e "${YELLOW}No CI runs found${NC}"
    exit 0
  fi
  
  echo "$WORKFLOWS" | jq -c '.[]' | while read -r workflow; do
    id=$(echo "$workflow" | jq -r '.databaseId')
    name=$(echo "$workflow" | jq -r '.workflowName')
    status=$(echo "$workflow" | jq -r '.status')
    conclusion=$(echo "$workflow" | jq -r '.conclusion')
    event=$(echo "$workflow" | jq -r '.event')
    
    # Display workflow info
    echo -e "${BOLD}$name${NC} (Triggered by: $event)"
    echo -e "Status: $(format_status "$status" "$conclusion")"
    echo -e "Details: gh run view $id"
    
    # Display job details for this workflow run
    echo "Jobs:"
    gh run view "$id" --json jobs | jq -r '.jobs[] | "  - \(.name): \(.status) \(.conclusion)"' | while read -r job_line; do
      job_name=$(echo "$job_line" | cut -d ':' -f 1)
      job_status=$(echo "$job_line" | cut -d ':' -f 2 | cut -d ' ' -f 2)
      job_conclusion=$(echo "$job_line" | cut -d ' ' -f 3)
      
      echo -e "$job_name: $(format_status "$job_status" "$job_conclusion")"
    done
    
    echo "----------------------------------------"
  done
}

# Run the main function
display_workflows
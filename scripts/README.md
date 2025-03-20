# Development Scripts

This directory contains utility scripts to help with development workflows.

## CI/CD Scripts

### `wait_for_pipeline.sh`

A simple script to wait for GitHub Actions pipelines to complete in the current PR.

```bash
# Wait for all PR checks to complete (default timeout: 15 minutes)
./wait_for_pipeline.sh

# Wait with a custom timeout (in seconds)
./wait_for_pipeline.sh 300  # Wait for 5 minutes
```

### `watch_ci.sh`

Advanced script for watching CI runs with various options.

```bash
# Watch current PR checks
./watch_ci.sh

# Watch a specific run by ID
./watch_ci.sh --run 12345678

# Watch the latest run of a specific workflow
./watch_ci.sh --workflow ci.yml

# Watch the latest run on a specific branch
./watch_ci.sh --branch feature/my-feature

# Set a custom timeout (in seconds)
./watch_ci.sh --timeout 300
```

### `ci_status.sh`

Visual summary of CI pipeline status with colorful output.

```bash
# Show status for current branch
./ci_status.sh

# Show status for a specific branch
./ci_status.sh --branch feature/my-feature

# Show status for a specific PR
./ci_status.sh --pr 36
```

## Requirements

These scripts require:

- GitHub CLI (`gh`) installed and authenticated
- `jq` for JSON processing (used in watch_ci.sh and ci_status.sh)
- Bash shell environment

## Installation

Make sure the scripts are executable:

```bash
chmod +x scripts/*.sh
```
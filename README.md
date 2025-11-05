# GitHub Actions Matrix Testing with Results Publishing

This repository demonstrates a GitHub Actions workflow that:
1. Dynamically generates a test matrix using Python
2. Runs tests across multiple environments
3. Collects and aggregates results with historical tracking
4. Automatically maintains a 2-week rolling history
5. Publishes results to a GitHub Pages repository as interactive HTML

## Files

- **hello.py** - Main test script that outputs structured JSON results
- **generate_matrix.py** - Dynamically generates the test matrix configuration
- **aggregate_results.py** - Aggregates all test results and generates HTML report
- **.github/workflows/hello-world.yml** - GitHub Actions workflow configuration

## Workflow Overview

The workflow consists of 3 jobs:

1. **generate-matrix** - Runs the Python script to generate the test matrix
2. **hello-world** - Executes tests across all matrix combinations and uploads results
3. **aggregate-and-publish** - Collects all results, generates HTML, and publishes to GitHub Pages

## Setup Instructions

### 1. Create a Personal Access Token (PAT)

1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Give it a descriptive name (e.g., "GH Pages Deploy Token")
4. Select the **repo** scope (full control of private repositories)
5. Generate the token and copy it

### 2. Add the Token as a Secret

1. In this repository, go to Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Name: `GH_PAGES_DEPLOY_TOKEN`
4. Value: Paste the token you copied
5. Click "Add secret"

### 3. Configure the GitHub Pages Repository

The workflow is already configured for repository `ggbecker/workflow-testing-pages`. If you want to change this:

In `.github/workflows/hello-world.yml`:
- Line 81: Update the `repository` field in the checkout step
- Line 98: Update the `external_repository` field in the publish step

```yaml
repository: YOUR_USERNAME/YOUR_PAGES_REPO
```

Also verify the `publish_branch` (line 82 and 99):
- Use `main` if your GitHub Pages repository uses the main branch
- Use `gh-pages` if it uses a gh-pages branch

### 4. Enable GitHub Pages in the Target Repository

1. Go to your GitHub Pages repository
2. Navigate to Settings → Pages
3. Under "Source", select the branch you're publishing to (main or gh-pages)
4. Click Save

## Customizing the Test Matrix

Edit `generate_matrix.py` to customize which environments to test. The function `generate_matrix()` can include any logic:

```python
def generate_matrix():
    # Example: Test only on Linux with Python 3.11+
    matrix = {
        "os": ["ubuntu-latest"],
        "python-version": ["3.11", "3.12"]
    }
    return matrix
```

## Historical Tracking and Retention

The workflow automatically maintains a historical record of test results:

- **Retention Period**: Results from the last 2 weeks are kept
- **Automatic Cleanup**: Results older than 2 weeks are automatically removed
- **Storage**: Each workflow run is saved in the `runs/` directory as a timestamped JSON file
- **Merging**: New results are merged with recent historical data on each run

### How it Works

1. Before publishing, the workflow checks out the existing GitHub Pages repository
2. It loads all previous runs from the `runs/` directory
3. Filters out runs older than 2 weeks
4. Adds the new run results
5. Regenerates the HTML report with all retained runs
6. Publishes everything back to GitHub Pages

### Customizing Retention Period

To change the 2-week retention period, edit `aggregate_results.py` line 342:

```python
filtered_runs = filter_old_runs(historical_runs, max_age_days=14)  # Change 14 to desired days
```

## Viewing Results

After the workflow runs successfully:
1. Results are published to your GitHub Pages repository
2. View the HTML report at: `https://YOUR_USERNAME.github.io/` (or your custom domain)
3. The report shows:
   - Summary of all test runs from the last 2 weeks
   - Expandable sections for each workflow run
   - All test environments with platform details
   - Latest run marked with a badge

## Local Testing

Test the scripts locally:

```bash
# Test the hello world script
python hello.py

# Test matrix generation
python generate_matrix.py

# Test aggregation (after creating artifacts directory with results)
mkdir -p artifacts
# ... copy some result.json files to artifacts/ ...
python aggregate_results.py
```

## Workflow Triggers

The workflow runs on:
- Push to main branch
- Pull requests to main branch
- Manual trigger (workflow_dispatch)

## Artifacts

Results from each matrix job are stored as artifacts for 30 days and can be downloaded from the Actions tab.

## GitHub Pages Repository Structure

After running the workflow, your GitHub Pages repository will have the following structure:

```
YOUR_PAGES_REPO/
├── index.html              # Main HTML report with all runs
└── runs/                   # Historical run data
    ├── 2025-11-05-14-30-15.json
    ├── 2025-11-04-10-22-33.json
    ├── 2025-11-03-08-15-42.json
    └── ...                 # One JSON file per workflow run
```

Each JSON file in the `runs/` directory contains:
- Timestamp of the run
- GitHub workflow run number and ID
- Array of results from all matrix environments tested in that run

## Features

- **Dynamic Matrix Generation**: Customize test environments based on any logic (date, environment variables, etc.)
- **Historical Tracking**: View results from all runs in the last 2 weeks
- **Interactive HTML**: Collapsible sections for each run with detailed environment information
- **Automatic Cleanup**: Old results are automatically removed to prevent repository bloat
- **Cross-Platform Testing**: Test across Linux, Windows, and macOS with multiple Python versions
- **Zero Maintenance**: Once set up, the workflow handles everything automatically

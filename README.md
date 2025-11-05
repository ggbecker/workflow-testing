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
3. **aggregate-and-publish** - Collects all results, generates HTML, publishes to GitHub Pages, and posts direct URLs to the workflow summary

### GitHub Actions Summary

After each workflow run, a detailed summary is automatically posted to the GitHub Actions summary page, including:
- Run information (run number, timestamp, environments tested)
- Direct links to the latest run
- Individual links to each environment result
- A summary table of all tested environments

To view the summary:
1. Go to the Actions tab in your repository
2. Click on a workflow run
3. The summary appears at the top with all direct links

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
- Line 93: Update the `PAGES_URL` environment variable
- Line 106: Update the full report URL
- Line 107: Update the `external_repository` field in the publish step

Example changes:
```yaml
repository: YOUR_USERNAME/YOUR_PAGES_REPO
PAGES_URL: https://YOUR_USERNAME.github.io/YOUR_PAGES_REPO
external_repository: YOUR_USERNAME/YOUR_PAGES_REPO
```

Also verify the `publish_branch` (line 82 and 108):
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
6. Publishes only `index.html` and `runs/` directory back to GitHub Pages
   - **Note**: The workflow uses `keep_files: true` to preserve any other files in your GitHub Pages repository
   - Only `index.html` and files in `runs/` directory are created/updated

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

### Sharing Direct Links

Each test run and environment result has a unique URL for easy sharing:

**Method 1: From GitHub Actions Summary**
1. Go to the Actions tab and click on a workflow run
2. The summary at the top contains direct links to all results
3. Click any link to jump directly to that specific result

**Method 2: From the HTML Report**
1. Click the "🔗 Link" button next to any run number to copy its URL
2. Click the "🔗" button on any environment card to copy its URL
3. The URL is automatically copied to your clipboard

**URL Examples:**
- Full run: `https://YOUR_USERNAME.github.io/#run-0`
- Specific environment: `https://YOUR_USERNAME.github.io/#env-0-1`

When someone visits these URLs:
- The page automatically scrolls to the linked result
- The relevant section automatically expands if collapsed
- The target element is highlighted briefly for easy identification

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
- **Direct URLs**: Each run and environment result has a unique URL that can be copied and shared
  - Click the "🔗 Link" button on any run to copy its direct URL
  - Click the "🔗" button on any environment card to copy its direct URL
  - URLs automatically expand the relevant section when accessed
- **GitHub Actions Integration**: Automatic summary posted to each workflow run with direct links to all results
- **Automatic Cleanup**: Old results are automatically removed to prevent repository bloat
- **Cross-Platform Testing**: Test across Linux, Windows, and macOS with multiple Python versions
- **Safe Publishing**: Only modifies `index.html` and `runs/` directory, preserving all other files in your GitHub Pages repository
- **Zero Maintenance**: Once set up, the workflow handles everything automatically

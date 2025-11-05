#!/usr/bin/env python3
"""Aggregate results from all matrix jobs and generate HTML report."""

import json
import os
from pathlib import Path
from datetime import datetime, timedelta


def collect_results(artifacts_dir):
    """Collect all result.json files from artifacts directory."""
    results = []
    artifacts_path = Path(artifacts_dir)

    if not artifacts_path.exists():
        print(f"Artifacts directory '{artifacts_dir}' does not exist")
        return results

    # Find all result.json files
    for result_file in artifacts_path.rglob("result.json"):
        try:
            with open(result_file, "r") as f:
                data = json.load(f)
                results.append(data)
                print(f"Loaded: {result_file}")
        except Exception as e:
            print(f"Error loading {result_file}: {e}")

    return results


def load_historical_runs(historical_dir):
    """Load historical runs from the GitHub Pages repository."""
    historical_runs = []
    runs_dir = Path(historical_dir) / "runs"

    if not runs_dir.exists():
        print(f"No historical runs directory found at {runs_dir}")
        return historical_runs

    # Load all run files
    for run_file in sorted(runs_dir.glob("*.json"), reverse=True):
        try:
            with open(run_file, "r") as f:
                run_data = json.load(f)
                historical_runs.append(run_data)
                print(f"Loaded historical run: {run_file.name}")
        except Exception as e:
            print(f"Error loading {run_file}: {e}")

    return historical_runs


def filter_old_runs(runs, max_age_days=14):
    """Filter out runs older than max_age_days."""
    cutoff_date = datetime.utcnow() - timedelta(days=max_age_days)
    filtered_runs = []

    for run in runs:
        try:
            # Parse the timestamp from the run
            run_timestamp = datetime.fromisoformat(run["timestamp"].replace("Z", "+00:00"))

            if run_timestamp >= cutoff_date:
                filtered_runs.append(run)
                print(f"Keeping run from {run_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                print(f"Filtering out old run from {run_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        except (KeyError, ValueError) as e:
            print(f"Error parsing timestamp for run: {e}")
            # Keep runs with invalid timestamps to be safe
            filtered_runs.append(run)

    return filtered_runs


def generate_html(all_runs):
    """Generate HTML report from all runs (historical + current)."""
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GitHub Actions Test Results - Historical View</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        h1 {
            color: #24292e;
            border-bottom: 2px solid #0366d6;
            padding-bottom: 10px;
        }
        .summary {
            background: white;
            padding: 20px;
            border-radius: 6px;
            margin-bottom: 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .result-item {
            margin: 8px 0;
            display: flex;
            justify-content: space-between;
        }
        .result-label {
            font-weight: 600;
            color: #586069;
        }
        .result-value {
            color: #24292e;
            text-align: right;
            max-width: 60%;
            word-break: break-word;
        }
        .run-section {
            background: white;
            padding: 20px;
            border-radius: 6px;
            margin-bottom: 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .run-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            cursor: pointer;
            padding: 10px;
            background: #f6f8fa;
            border-radius: 6px;
            margin-bottom: 15px;
        }
        .run-header:hover {
            background: #e1e4e8;
        }
        .run-header h2 {
            margin: 0;
            color: #0366d6;
        }
        .run-meta {
            font-size: 0.9em;
            color: #6a737d;
        }
        .results-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }
        .result-card {
            background: #f6f8fa;
            padding: 15px;
            border-radius: 6px;
            border-left: 4px solid #28a745;
        }
        .result-card h3 {
            margin-top: 0;
            font-size: 1em;
            color: #0366d6;
        }
        .result-card .result-item {
            margin: 5px 0;
            font-size: 0.9em;
        }
        .timestamp {
            font-size: 0.85em;
            color: #6a737d;
        }
        .toggle-icon {
            font-size: 1.2em;
        }
        .run-content {
            display: block;
        }
        .run-content.collapsed {
            display: none;
        }
        footer {
            margin-top: 40px;
            text-align: center;
            color: #6a737d;
            font-size: 0.9em;
        }
        .badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 12px;
            background: #28a745;
            color: white;
            font-size: 0.8em;
            font-weight: 600;
        }
    </style>
    <script>
        function toggleRun(runId) {
            const content = document.getElementById('run-' + runId);
            const icon = document.getElementById('icon-' + runId);
            if (content.classList.contains('collapsed')) {
                content.classList.remove('collapsed');
                icon.textContent = '▼';
            } else {
                content.classList.add('collapsed');
                icon.textContent = '▶';
            }
        }
    </script>
</head>
<body>
    <h1>GitHub Actions Test Results - Historical View</h1>
"""

    # Summary section
    total_runs = len(all_runs)
    total_environments = sum(len(run.get("results", [])) for run in all_runs)

    html += f"""
    <div class="summary">
        <h2>Summary</h2>
        <div class="result-item">
            <span class="result-label">Total Test Runs (Last 2 Weeks):</span>
            <span class="result-value">{total_runs}</span>
        </div>
        <div class="result-item">
            <span class="result-label">Total Environments Tested:</span>
            <span class="result-value">{total_environments}</span>
        </div>
        <div class="result-item">
            <span class="result-label">Report Generated:</span>
            <span class="result-value timestamp">{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</span>
        </div>
    </div>
"""

    # Generate sections for each run
    for idx, run in enumerate(all_runs):
        run_timestamp = run.get("timestamp", "Unknown")
        run_number = run.get("run_number", "N/A")
        results = run.get("results", [])
        is_latest = idx == 0

        try:
            formatted_time = datetime.fromisoformat(run_timestamp.replace("Z", "+00:00")).strftime('%Y-%m-%d %H:%M:%S UTC')
        except:
            formatted_time = run_timestamp

        badge_html = '<span class="badge">LATEST</span> ' if is_latest else ''

        html += f"""
    <div class="run-section">
        <div class="run-header" onclick="toggleRun({idx})">
            <div>
                <h2>{badge_html}Run #{run_number}</h2>
                <div class="run-meta">{formatted_time} - {len(results)} environments tested</div>
            </div>
            <span class="toggle-icon" id="icon-{idx}">▼</span>
        </div>
        <div class="run-content" id="run-{idx}">
            <div class="results-grid">
"""

        # Add result cards for this run
        for env_idx, result in enumerate(results, 1):
            python_info = result.get('python_version_info', {})
            python_ver = f"{python_info.get('major', '?')}.{python_info.get('minor', '?')}.{python_info.get('micro', '?')}"

            html += f"""
                <div class="result-card">
                    <h3>{result.get('system', 'Unknown')} - Python {python_ver}</h3>
                    <div class="result-item">
                        <span class="result-label">Platform:</span>
                        <span class="result-value">{result.get('platform', 'N/A')}</span>
                    </div>
                    <div class="result-item">
                        <span class="result-label">Architecture:</span>
                        <span class="result-value">{result.get('architecture', 'N/A')}</span>
                    </div>
                    <div class="result-item">
                        <span class="result-label">Machine:</span>
                        <span class="result-value">{result.get('machine', 'N/A')}</span>
                    </div>
                </div>
"""

        html += """
            </div>
        </div>
    </div>
"""

    html += """
    <footer>
        <p>Generated by GitHub Actions Workflow - Automatically removes runs older than 2 weeks</p>
    </footer>
</body>
</html>
"""

    return html


def main():
    """Main function to aggregate results and generate HTML."""
    artifacts_dir = os.getenv("ARTIFACTS_DIR", "artifacts")
    output_dir = os.getenv("OUTPUT_DIR", "output")
    historical_dir = os.getenv("HISTORICAL_DIR", "")

    # Create output directory and runs subdirectory
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    runs_output_dir = Path(output_dir) / "runs"
    runs_output_dir.mkdir(parents=True, exist_ok=True)

    # Collect current run results
    print("Collecting current run results...")
    current_results = collect_results(artifacts_dir)

    if not current_results:
        print("Warning: No results found for current run!")

    print(f"Found {len(current_results)} results for current run")

    # Create current run object
    current_run = {
        "timestamp": datetime.utcnow().isoformat(),
        "run_number": os.getenv("GITHUB_RUN_NUMBER", "local"),
        "run_id": os.getenv("GITHUB_RUN_ID", "local"),
        "results": current_results
    }

    # Load historical runs
    all_runs = []
    if historical_dir and Path(historical_dir).exists():
        print(f"\nLoading historical runs from {historical_dir}...")
        historical_runs = load_historical_runs(historical_dir)
        print(f"Loaded {len(historical_runs)} historical runs")

        # Filter out runs older than 2 weeks
        print("\nFiltering old runs (keeping last 2 weeks)...")
        filtered_runs = filter_old_runs(historical_runs, max_age_days=14)
        print(f"Kept {len(filtered_runs)} runs after filtering")

        all_runs = filtered_runs
    else:
        print(f"\nNo historical directory found at {historical_dir}, starting fresh")

    # Add current run to the beginning (most recent)
    all_runs.insert(0, current_run)
    print(f"\nTotal runs to include: {len(all_runs)}")

    # Save each run as a separate JSON file
    print("\nSaving run files...")
    for run in all_runs:
        timestamp = run.get("timestamp", datetime.utcnow().isoformat())
        # Create a safe filename from timestamp
        safe_timestamp = timestamp.replace(":", "-").replace(".", "-").split("+")[0]
        run_filename = f"{safe_timestamp}.json"
        run_filepath = runs_output_dir / run_filename

        with open(run_filepath, "w") as f:
            json.dump(run, f, indent=2)
        print(f"  Saved: {run_filename}")

    # Generate and save HTML
    print("\nGenerating HTML report...")
    html_content = generate_html(all_runs)
    html_output = Path(output_dir) / "index.html"
    with open(html_output, "w") as f:
        f.write(html_content)
    print(f"Generated HTML report at {html_output}")

    # Summary
    print("\n" + "="*50)
    print("SUMMARY")
    print("="*50)
    print(f"Total runs: {len(all_runs)}")
    print(f"Total environments in all runs: {sum(len(run.get('results', [])) for run in all_runs)}")
    print(f"Runs directory: {runs_output_dir}")
    print(f"HTML report: {html_output}")
    print("="*50)


if __name__ == "__main__":
    main()

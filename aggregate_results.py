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


def load_runs_from_output(output_base_dir):
    """Load existing runs from timestamped folders in output directory."""
    runs = []
    output_path = Path(output_base_dir)

    if not output_path.exists():
        print(f"Output directory '{output_base_dir}' does not exist")
        return runs

    # Find all timestamped folders (format: YYYY-MM-DD-HH-MM-SS)
    for run_folder in sorted(output_path.iterdir(), reverse=True):
        if run_folder.is_dir() and not run_folder.name.startswith('.'):
            # Check if folder name looks like a timestamp
            if len(run_folder.name) > 10 and '-' in run_folder.name:
                try:
                    # Convert folder name back to ISO timestamp
                    folder_timestamp = run_folder.name.replace("-", ":", 2)  # Replace first 2 hyphens with colons
                    folder_timestamp = folder_timestamp.replace("-", ":", 1)  # Replace third hyphen with colon

                    # Create run data placeholder
                    run_data = {
                        "timestamp": folder_timestamp,
                        "run_number": "N/A",
                        "run_id": "N/A",
                        "results": [],  # Will be populated if needed
                        "folder_path": str(run_folder)
                    }
                    runs.append(run_data)
                    print(f"  Found run folder: {run_folder.name}")
                except Exception as e:
                    print(f"  Error parsing folder {run_folder.name}: {e}")

    return runs


def delete_old_run_folders(runs_to_delete):
    """Delete folders for old runs from disk."""
    import shutil

    for run in runs_to_delete:
        folder_path = run.get("folder_path")
        if folder_path and Path(folder_path).exists():
            try:
                shutil.rmtree(folder_path)
                print(f"  Deleted old run folder: {folder_path}")
            except Exception as e:
                print(f"  Error deleting folder {folder_path}: {e}")


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
        .link-button {
            display: inline-block;
            padding: 4px 8px;
            margin-left: 8px;
            background: #0366d6;
            color: white;
            border-radius: 4px;
            text-decoration: none;
            font-size: 0.75em;
            cursor: pointer;
            transition: background 0.2s;
        }
        .link-button:hover {
            background: #0256c7;
        }
        .link-button:active {
            background: #024ea5;
        }
        .copy-notification {
            display: none;
            position: fixed;
            top: 20px;
            right: 20px;
            background: #28a745;
            color: white;
            padding: 12px 20px;
            border-radius: 6px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
            z-index: 1000;
            animation: slideIn 0.3s ease-out;
        }
        .copy-notification.show {
            display: block;
        }
        @keyframes slideIn {
            from {
                transform: translateX(400px);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        .run-section:target {
            animation: highlight 2s ease-out;
        }
        @keyframes highlight {
            0% {
                background: #fff3cd;
            }
            100% {
                background: white;
            }
        }
        .result-card:target {
            animation: highlight-card 2s ease-out;
            border-left-color: #0366d6;
        }
        @keyframes highlight-card {
            0% {
                background: #fff3cd;
            }
            100% {
                background: #f6f8fa;
            }
        }
        .env-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
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

        function copyLink(anchor) {
            const url = window.location.origin + window.location.pathname + '#' + anchor;

            // Copy to clipboard
            if (navigator.clipboard && navigator.clipboard.writeText) {
                navigator.clipboard.writeText(url).then(() => {
                    showNotification('Link copied to clipboard!');
                }).catch(err => {
                    // Fallback method
                    fallbackCopy(url);
                });
            } else {
                // Fallback for older browsers
                fallbackCopy(url);
            }
        }

        function fallbackCopy(text) {
            const textArea = document.createElement('textarea');
            textArea.value = text;
            textArea.style.position = 'fixed';
            textArea.style.left = '-999999px';
            document.body.appendChild(textArea);
            textArea.select();
            try {
                document.execCommand('copy');
                showNotification('Link copied to clipboard!');
            } catch (err) {
                showNotification('Failed to copy link');
            }
            document.body.removeChild(textArea);
        }

        function showNotification(message) {
            const notification = document.getElementById('copy-notification');
            notification.textContent = message;
            notification.classList.add('show');
            setTimeout(() => {
                notification.classList.remove('show');
            }, 2000);
        }

        // On page load, expand the section if there's a hash
        window.addEventListener('DOMContentLoaded', () => {
            if (window.location.hash) {
                const hash = window.location.hash.substring(1);

                // Check if it's an environment result
                if (hash.startsWith('env-')) {
                    const parts = hash.split('-');
                    if (parts.length >= 2) {
                        const runId = parts[1];
                        const content = document.getElementById('run-' + runId);
                        const icon = document.getElementById('icon-' + runId);
                        if (content && content.classList.contains('collapsed')) {
                            content.classList.remove('collapsed');
                            if (icon) icon.textContent = '▼';
                        }
                    }
                }
                // Check if it's a run section
                else if (hash.startsWith('run-')) {
                    const runId = hash.replace('run-', '');
                    const content = document.getElementById('run-' + runId);
                    const icon = document.getElementById('icon-' + runId);
                    if (content && content.classList.contains('collapsed')) {
                        content.classList.remove('collapsed');
                        if (icon) icon.textContent = '▼';
                    }
                }

                // Scroll to the element
                setTimeout(() => {
                    const element = document.getElementById(hash);
                    if (element) {
                        element.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    }
                }, 100);
            }
        });
    </script>
</head>
<body>
    <div id="copy-notification" class="copy-notification"></div>
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
        run_id = run.get("run_id", "N/A")
        results = run.get("results", [])
        is_latest = idx == 0

        try:
            formatted_time = datetime.fromisoformat(run_timestamp.replace("Z", "+00:00")).strftime('%Y-%m-%d %H:%M:%S UTC')
        except:
            formatted_time = run_timestamp

        badge_html = '<span class="badge">LATEST</span> ' if is_latest else ''
        anchor_id = f"run-{idx}"

        html += f"""
    <div class="run-section" id="{anchor_id}">
        <div class="run-header" onclick="toggleRun({idx})">
            <div>
                <h2>
                    {badge_html}Run #{run_number}
                    <button class="link-button" onclick="event.stopPropagation(); copyLink('{anchor_id}');" title="Copy link to this run">🔗 Link</button>
                </h2>
                <div class="run-meta">{formatted_time} - {len(results)} environments tested - Run ID: {run_id}</div>
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
            env_anchor_id = f"env-{idx}-{env_idx}"

            html += f"""
                <div class="result-card" id="{env_anchor_id}">
                    <div class="env-header">
                        <h3>{result.get('system', 'Unknown')} - Python {python_ver}</h3>
                        <button class="link-button" onclick="copyLink('{env_anchor_id}');" title="Copy link to this environment">🔗</button>
                    </div>
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


def collect_html_rows(artifacts_dir):
    """Collect all result.html files from artifacts directory."""
    html_rows = []
    artifacts_path = Path(artifacts_dir)

    if not artifacts_path.exists():
        print(f"Artifacts directory '{artifacts_dir}' does not exist")
        return html_rows

    # Find all result.html files
    for html_file in sorted(artifacts_path.rglob("result.html")):
        try:
            with open(html_file, "r") as f:
                row_content = f.read().strip()
                html_rows.append(row_content)
                print(f"Loaded HTML row: {html_file}")
        except Exception as e:
            print(f"Error loading {html_file}: {e}")

    return html_rows


def generate_pr_results_html(html_rows, pr_number, base_url):
    """Generate table-based HTML for PR test results."""
    num_envs = len(html_rows)
    generated_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pull Request Test Results</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        h1 {{
            color: #24292e;
            border-bottom: 2px solid #6f42c1;
            padding-bottom: 10px;
        }}
        .pr-badge {{
            display: inline-block;
            padding: 4px 12px;
            background: #6f42c1;
            color: white;
            border-radius: 4px;
            font-size: 0.9em;
            margin-left: 10px;
        }}
        .summary {{
            background: white;
            padding: 20px;
            border-radius: 6px;
            margin-bottom: 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }}
        .info-item {{
            background: #f6f8fa;
            padding: 12px;
            border-radius: 4px;
            border-left: 3px solid #6f42c1;
        }}
        .info-label {{
            font-size: 0.85em;
            color: #586069;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .info-value {{
            font-size: 1.2em;
            color: #24292e;
            margin-top: 5px;
        }}
        table {{
            width: 100%;
            background: white;
            border-collapse: collapse;
            border-radius: 6px;
            overflow: hidden;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        thead {{
            background: #f6f8fa;
            border-bottom: 2px solid #e1e4e8;
        }}
        th {{
            padding: 12px;
            text-align: left;
            font-weight: 600;
            color: #24292e;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        td {{
            padding: 12px;
            border-bottom: 1px solid #e1e4e8;
            color: #24292e;
        }}
        tr:last-child td {{
            border-bottom: none;
        }}
        tr:hover {{
            background-color: #f6f8fa;
        }}
        footer {{
            margin-top: 40px;
            text-align: center;
            color: #6a737d;
            font-size: 0.9em;
        }}
        .back-link {{
            display: inline-block;
            margin-top: 20px;
            padding: 8px 16px;
            background: #0366d6;
            color: white;
            text-decoration: none;
            border-radius: 4px;
            transition: background 0.2s;
        }}
        .back-link:hover {{
            background: #0256c7;
        }}
    </style>
</head>
<body>
    <h1>Pull Request Test Results <span class="pr-badge">PR #{pr_number}</span></h1>

    <div class="summary">
        <h2>Summary</h2>
        <div class="info-grid">
            <div class="info-item">
                <div class="info-label">Environments Tested</div>
                <div class="info-value">{num_envs}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Test Type</div>
                <div class="info-value">Fast PR Tests</div>
            </div>
            <div class="info-item">
                <div class="info-label">Generated</div>
                <div class="info-value">{generated_time}</div>
            </div>
        </div>
    </div>

    <table>
        <thead>
            <tr>
                <th>Timestamp</th>
                <th>System</th>
                <th>Python Version</th>
                <th>Platform</th>
                <th>Architecture</th>
                <th>Machine</th>
                <th>Status</th>
            </tr>
        </thead>
        <tbody>
"""

    # Add all the HTML rows
    for row in html_rows:
        html += row + "\n"

    html += f"""
        </tbody>
    </table>

    <a href="{base_url}" class="back-link">← View Full Historical Results</a>

    <footer>
        <p>Pull Request Test Results - Faster subset of tests for quick feedback</p>
    </footer>
</body>
</html>
"""

    return html


def generate_github_summary(current_run, base_url, safe_timestamp, test_folder="full-tests"):
    """Generate markdown summary for GitHub Actions step summary."""
    run_number = current_run.get("run_number", "N/A")
    run_id = current_run.get("run_id", "N/A")
    timestamp = current_run.get("timestamp", "Unknown")
    results = current_run.get("results", [])

    try:
        formatted_time = datetime.fromisoformat(timestamp.replace("Z", "+00:00")).strftime('%Y-%m-%d %H:%M:%S UTC')
    except:
        formatted_time = timestamp

    # Build URL to this specific run
    run_url = f"{base_url}/{test_folder}/{safe_timestamp}/"

    # Start building the markdown
    markdown = f"""# 🎯 Test Results Summary

## Run Information
- **Run Number**: #{run_number}
- **Run ID**: {run_id}
- **Timestamp**: {formatted_time}
- **Environments Tested**: {len(results)}

## 🔗 Direct Links

### Latest Run
- [View This Run's Results]({run_url}) - Direct link to this test run

### Individual Environment Results

"""

    # Add links for each environment
    for idx, result in enumerate(results, 1):
        python_info = result.get('python_version_info', {})
        python_ver = f"{python_info.get('major', '?')}.{python_info.get('minor', '?')}.{python_info.get('micro', '?')}"
        system = result.get('system', 'Unknown')
        platform_name = result.get('platform', 'N/A')

        env_anchor = f"env-0-{idx}"
        markdown += f"- [{system} - Python {python_ver}]({run_url}#{env_anchor})\n"
        markdown += f"  - Platform: `{platform_name}`\n"
        markdown += f"  - Architecture: `{result.get('architecture', 'N/A')}`\n\n"

    markdown += f"""
## 📊 Results Overview

| Environment | Python Version | Platform | Status |
|------------|----------------|----------|--------|
"""

    for result in results:
        python_info = result.get('python_version_info', {})
        python_ver = f"{python_info.get('major', '?')}.{python_info.get('minor', '?')}.{python_info.get('micro', '?')}"
        system = result.get('system', 'Unknown')
        platform_name = result.get('platform', 'N/A')

        markdown += f"| {system} | {python_ver} | {platform_name} | ✅ |\n"

    markdown += f"""
---

💡 **Tip**: Click any link above to view detailed results for that specific environment.

📅 **Retention**: Results are kept for 2 weeks and then automatically cleaned up.
"""

    return markdown


def generate_main_index_html(base_url):
    """Generate main landing page index.html."""
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Results - Workflow Testing</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            max-width: 1000px;
            margin: 0 auto;
            padding: 40px 20px;
            background-color: #f5f5f5;
        }}
        h1 {{
            color: #24292e;
            border-bottom: 3px solid #0366d6;
            padding-bottom: 15px;
            text-align: center;
        }}
        .intro {{
            text-align: center;
            color: #586069;
            margin-bottom: 40px;
        }}
        .cards-container {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 30px;
            margin-top: 30px;
        }}
        .card {{
            background: white;
            border-radius: 8px;
            padding: 30px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            transition: transform 0.2s, box-shadow 0.2s;
            text-decoration: none;
            color: inherit;
            display: block;
        }}
        .card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 4px 16px rgba(0,0,0,0.15);
        }}
        .card-icon {{
            font-size: 3em;
            margin-bottom: 15px;
        }}
        .card-title {{
            font-size: 1.5em;
            font-weight: 600;
            color: #24292e;
            margin-bottom: 10px;
        }}
        .card-description {{
            color: #586069;
            line-height: 1.6;
            margin-bottom: 15px;
        }}
        .card-meta {{
            font-size: 0.9em;
            color: #6a737d;
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid #e1e4e8;
        }}
        .card-meta strong {{
            color: #24292e;
        }}
        .full-tests-card {{
            border-left: 4px solid #0366d6;
        }}
        .pr-tests-card {{
            border-left: 4px solid #6f42c1;
        }}
        .comprehensive-tests-card {{
            border-left: 4px solid #28a745;
        }}
        footer {{
            text-align: center;
            margin-top: 60px;
            color: #6a737d;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <h1>🧪 Test Results Dashboard</h1>
    <p class="intro">View comprehensive test results from GitHub Actions workflows</p>

    <div class="cards-container">
        <a href="{base_url}/full-tests/" class="card full-tests-card">
            <div class="card-icon">📊</div>
            <div class="card-title">Full Test Results</div>
            <div class="card-description">
                Comprehensive test results from pushes to main branch. Includes all platforms and Python versions with historical tracking.
            </div>
            <div class="card-meta">
                <strong>Coverage:</strong> Linux, Windows, macOS<br>
                <strong>Python:</strong> 3.9, 3.10, 3.11, 3.12<br>
                <strong>Retention:</strong> 2 weeks
            </div>
        </a>

        <a href="{base_url}/pr-tests/" class="card pr-tests-card">
            <div class="card-icon">⚡</div>
            <div class="card-title">PR Test Results</div>
            <div class="card-description">
                Fast test results from pull requests. Minimal subset of tests for quick feedback during code review.
            </div>
            <div class="card-meta">
                <strong>Coverage:</strong> Ubuntu Latest<br>
                <strong>Python:</strong> 3.11, 3.12<br>
                <strong>Purpose:</strong> Quick validation
            </div>
        </a>

        <a href="{base_url}/comprehensive-tests/" class="card comprehensive-tests-card">
            <div class="card-icon">🔬</div>
            <div class="card-title">Comprehensive Tests (Manual)</div>
            <div class="card-description">
                Extensive manual test results across all platforms and Python versions. Includes older OS versions for maximum compatibility testing.
            </div>
            <div class="card-meta">
                <strong>Coverage:</strong> Ubuntu (latest & 20.04), Windows (latest & 2019), macOS (latest & 12)<br>
                <strong>Python:</strong> 3.8, 3.9, 3.10, 3.11, 3.12<br>
                <strong>Trigger:</strong> Manual only
            </div>
        </a>
    </div>

    <footer>
        <p>🤖 Generated by GitHub Actions Workflow</p>
        <p>Results are automatically updated with each workflow run</p>
    </footer>
</body>
</html>
"""
    return html


def generate_listing_page_html(runs, test_type, base_url):
    """Generate listing page for full-tests, pr-tests, or comprehensive-tests."""
    type_config = {
        "full": {
            "title": "Full Test Results",
            "icon": "📊",
            "description": "Comprehensive test results from pushes to main",
            "color": "#0366d6"
        },
        "pr": {
            "title": "Pull Request Test Results",
            "icon": "⚡",
            "description": "Fast test results from pull requests",
            "color": "#6f42c1"
        },
        "comprehensive": {
            "title": "Comprehensive Tests (Manual)",
            "icon": "🔬",
            "description": "Extensive manual test results across all platforms and versions",
            "color": "#28a745"
        }
    }

    config = type_config.get(test_type, type_config["full"])

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{config['title']}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        h1 {{
            color: #24292e;
            border-bottom: 3px solid {config['color']};
            padding-bottom: 10px;
        }}
        .icon {{
            font-size: 1.5em;
        }}
        .description {{
            color: #586069;
            margin-bottom: 30px;
        }}
        .back-link {{
            display: inline-block;
            margin-bottom: 20px;
            color: #0366d6;
            text-decoration: none;
        }}
        .back-link:hover {{
            text-decoration: underline;
        }}
        table {{
            width: 100%;
            background: white;
            border-collapse: collapse;
            border-radius: 6px;
            overflow: hidden;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        thead {{
            background: #f6f8fa;
            border-bottom: 2px solid #e1e4e8;
        }}
        th {{
            padding: 12px;
            text-align: left;
            font-weight: 600;
            color: #24292e;
            font-size: 0.9em;
            text-transform: uppercase;
        }}
        td {{
            padding: 12px;
            border-bottom: 1px solid #e1e4e8;
            color: #24292e;
        }}
        tr:last-child td {{
            border-bottom: none;
        }}
        tr:hover {{
            background-color: #f6f8fa;
        }}
        .badge {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 3px;
            font-size: 0.85em;
            font-weight: 600;
        }}
        .badge-latest {{
            background: #28a745;
            color: white;
        }}
        .view-link {{
            color: #0366d6;
            text-decoration: none;
            font-weight: 600;
        }}
        .view-link:hover {{
            text-decoration: underline;
        }}
        footer {{
            margin-top: 40px;
            text-align: center;
            color: #6a737d;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <a href="{base_url}" class="back-link">← Back to Dashboard</a>

    <h1><span class="icon">{config['icon']}</span> {config['title']}</h1>
    <p class="description">{config['description']}</p>

    <table>
        <thead>
            <tr>
                <th>Run</th>
                <th>Timestamp</th>
                <th>Run Number</th>
                <th>Environments</th>
                <th>Action</th>
            </tr>
        </thead>
        <tbody>
"""

    for idx, run in enumerate(runs):
        timestamp = run.get("timestamp", "Unknown")
        run_number = run.get("run_number", "N/A")
        run_id = run.get("run_id", "N/A")
        num_envs = len(run.get("results", []))

        # Create safe timestamp for URL
        safe_timestamp = timestamp.replace(":", "-").replace(".", "-").split("+")[0]

        try:
            formatted_time = datetime.fromisoformat(timestamp.replace("Z", "+00:00")).strftime('%Y-%m-%d %H:%M:%S UTC')
        except:
            formatted_time = timestamp

        badge_html = '<span class="badge badge-latest">LATEST</span>' if idx == 0 else ''

        html += f"""
            <tr>
                <td>{badge_html} #{run_number}</td>
                <td>{formatted_time}</td>
                <td>Run ID: {run_id}</td>
                <td>{num_envs} environments</td>
                <td><a href="./{safe_timestamp}/" class="view-link">View Results →</a></td>
            </tr>
"""

    html += """
        </tbody>
    </table>

    <footer>
        <p>Results are kept for 2 weeks and automatically cleaned up</p>
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
    is_pull_request = os.getenv("IS_PULL_REQUEST", "false") == "true"
    is_comprehensive = os.getenv("IS_COMPREHENSIVE", "false") == "true"
    pr_number = os.getenv("PR_NUMBER", "unknown")
    test_description = os.getenv("TEST_DESCRIPTION", "")
    base_url = os.getenv("PAGES_URL", "https://ggbecker.github.io/workflow-testing-pages")

    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Generate current run timestamp
    current_timestamp = datetime.utcnow().isoformat()
    safe_timestamp = current_timestamp.replace(":", "-").replace(".", "-").split("+")[0]

    # Handle Pull Request
    if is_pull_request:
        print("=" * 60)
        print("PULL REQUEST MODE - Generating table-based results")
        print("=" * 60)

        # Collect HTML rows from artifacts
        print("\nCollecting HTML rows...")
        html_rows = collect_html_rows(artifacts_dir)

        if not html_rows:
            print("Warning: No HTML rows found!")

        print(f"Found {len(html_rows)} HTML rows")

        # Create PR-specific directory structure: pr-tests/TIMESTAMP/
        pr_base_dir = Path(output_dir) / "pr-tests"
        pr_base_dir.mkdir(parents=True, exist_ok=True)

        # Load existing PR runs from output directory
        print(f"\nLoading existing PR runs from {pr_base_dir}...")
        pr_runs = load_runs_from_output(pr_base_dir)
        print(f"Found {len(pr_runs)} existing PR runs")

        # Filter old runs and delete their folders
        print("\nFiltering old PR runs (keeping last 2 weeks)...")
        cutoff_date = datetime.utcnow() - timedelta(days=14)
        old_runs = []
        kept_runs = []

        for run in pr_runs:
            try:
                run_timestamp = datetime.fromisoformat(run["timestamp"].replace("Z", "+00:00"))
                if run_timestamp >= cutoff_date:
                    kept_runs.append(run)
                    print(f"  Keeping run from {run_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
                else:
                    old_runs.append(run)
                    print(f"  Marking for deletion: run from {run_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            except (KeyError, ValueError) as e:
                print(f"  Error parsing timestamp for run: {e}")
                kept_runs.append(run)  # Keep runs with invalid timestamps

        # Delete old run folders
        if old_runs:
            print(f"\nDeleting {len(old_runs)} old run folders...")
            delete_old_run_folders(old_runs)

        pr_runs = kept_runs
        print(f"Kept {len(pr_runs)} PR runs after filtering")

        # Create new run folder and generate HTML
        pr_run_dir = pr_base_dir / safe_timestamp
        pr_run_dir.mkdir(parents=True, exist_ok=True)

        print("\nGenerating PR results HTML...")
        pr_html = generate_pr_results_html(html_rows, pr_number, base_url)
        pr_html_output = pr_run_dir / "index.html"
        with open(pr_html_output, "w", encoding="utf-8") as f:
            f.write(pr_html)
        print(f"Generated PR results at {pr_html_output}")

        # Add current run
        current_pr_run = {
            "timestamp": current_timestamp,
            "run_number": pr_number,
            "run_id": os.getenv("GITHUB_RUN_ID", "N/A"),
            "results": html_rows
        }
        pr_runs.insert(0, current_pr_run)

        # Generate PR listing page
        print("\nGenerating PR listing page...")
        pr_listing_html = generate_listing_page_html(pr_runs, "pr", base_url)
        pr_listing_output = pr_base_dir / "index.html"
        with open(pr_listing_output, "w", encoding="utf-8") as f:
            f.write(pr_listing_html)
        print(f"Generated PR listing at {pr_listing_output}")

        # Generate main index if it doesn't exist
        main_index_path = Path(output_dir) / "index.html"
        if not main_index_path.exists() or True:  # Always regenerate
            print("\nGenerating main index...")
            main_index_html = generate_main_index_html(base_url)
            with open(main_index_path, "w", encoding="utf-8") as f:
                f.write(main_index_html)
            print(f"Generated main index at {main_index_path}")

        # Summary
        print("\n" + "=" * 60)
        print("PR RESULTS SUMMARY")
        print("=" * 60)
        print(f"PR Number: {pr_number}")
        print(f"Environments tested: {len(html_rows)}")
        print(f"Results page: {pr_html_output}")
        print(f"Listing page: {pr_listing_output}")
        print("=" * 60)

        return

    # Determine test type and folder
    if is_comprehensive:
        test_type = "comprehensive"
        test_folder = "comprehensive-tests"
        test_title = "Comprehensive Tests (Manual)"
        print("=" * 60)
        print("COMPREHENSIVE MODE - Generating extensive test results")
        print("=" * 60)
    else:
        test_type = "full"
        test_folder = "full-tests"
        test_title = "Full Test Results"
        print("=" * 60)
        print("PUSH MODE - Generating comprehensive results")
        print("=" * 60)

    # Collect current run results
    print("\nCollecting current run results...")
    current_results = collect_results(artifacts_dir)

    if not current_results:
        print("Warning: No results found for current run!")

    print(f"Found {len(current_results)} results for current run")

    # Create test directory structure: {test_folder}/TIMESTAMP/
    test_base_dir = Path(output_dir) / test_folder
    test_base_dir.mkdir(parents=True, exist_ok=True)

    # Load existing test runs from output directory
    print(f"\nLoading existing {test_title.lower()} from {test_base_dir}...")
    all_runs = load_runs_from_output(test_base_dir)
    print(f"Found {len(all_runs)} existing {test_title.lower()}")

    # Filter old runs and delete their folders
    print("\nFiltering old runs (keeping last 2 weeks)...")
    cutoff_date = datetime.utcnow() - timedelta(days=14)
    old_runs = []
    kept_runs = []

    for run in all_runs:
        try:
            run_timestamp = datetime.fromisoformat(run["timestamp"].replace("Z", "+00:00"))
            if run_timestamp >= cutoff_date:
                kept_runs.append(run)
                print(f"  Keeping run from {run_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                old_runs.append(run)
                print(f"  Marking for deletion: run from {run_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        except (KeyError, ValueError) as e:
            print(f"  Error parsing timestamp for run: {e}")
            kept_runs.append(run)  # Keep runs with invalid timestamps

    # Delete old run folders
    if old_runs:
        print(f"\nDeleting {len(old_runs)} old run folders...")
        delete_old_run_folders(old_runs)

    all_runs = kept_runs
    print(f"Kept {len(all_runs)} runs after filtering")

    # Create current run object
    current_run = {
        "timestamp": current_timestamp,
        "run_number": os.getenv("GITHUB_RUN_NUMBER", "local"),
        "run_id": os.getenv("GITHUB_RUN_ID", "local"),
        "results": current_results
    }

    # Create new run folder and generate HTML
    test_run_dir = test_base_dir / safe_timestamp
    test_run_dir.mkdir(parents=True, exist_ok=True)

    print("\nGenerating run results HTML...")
    run_html = generate_html([current_run])  # Pass as list with single run
    run_html_output = test_run_dir / "index.html"
    with open(run_html_output, "w", encoding="utf-8") as f:
        f.write(run_html)
    print(f"Generated run results at {run_html_output}")

    # Add current run
    all_runs.insert(0, current_run)
    print(f"\nTotal runs to include: {len(all_runs)}")

    # Generate tests listing page
    print(f"\nGenerating {test_title.lower()} listing page...")
    test_listing_html = generate_listing_page_html(all_runs, test_type, base_url)
    test_listing_output = test_base_dir / "index.html"
    with open(test_listing_output, "w", encoding="utf-8") as f:
        f.write(test_listing_html)
    print(f"Generated {test_title.lower()} listing at {test_listing_output}")

    # Generate main index
    print("\nGenerating main index...")
    main_index_html = generate_main_index_html(base_url)
    main_index_path = Path(output_dir) / "index.html"
    with open(main_index_path, "w", encoding="utf-8") as f:
        f.write(main_index_html)
    print(f"Generated main index at {main_index_path}")

    # Generate GitHub Actions summary
    print("\nGenerating GitHub Actions summary...")
    github_summary = generate_github_summary(current_run, base_url, safe_timestamp, test_folder)
    summary_output = Path(output_dir) / "summary.md"
    with open(summary_output, "w", encoding="utf-8") as f:
        f.write(github_summary)
    print(f"Generated GitHub Actions summary at {summary_output}")

    # Summary
    print("\n" + "=" * 60)
    print(f"{test_title.upper()} SUMMARY")
    print("=" * 60)
    print(f"Total runs: {len(all_runs)}")
    print(f"Total environments in current run: {len(current_results)}")
    print(f"Run results: {run_html_output}")
    print(f"Listing page: {test_listing_output}")
    print(f"Main index: {main_index_path}")
    if test_description:
        print(f"Description: {test_description}")
    print("=" * 60)


if __name__ == "__main__":
    main()

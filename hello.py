#!/usr/bin/env python3
"""Simple Hello World script for testing GitHub Actions."""

import sys
import platform
import json
import os
from datetime import datetime


def generate_html_row(results):
    """Generate HTML table row from results."""
    python_ver = f"{results['python_version_info']['major']}.{results['python_version_info']['minor']}.{results['python_version_info']['micro']}"

    # Status badge (always success for now, can be extended)
    status_badge = '<span style="background: #28a745; color: white; padding: 2px 8px; border-radius: 3px; font-size: 0.85em;">✓ Pass</span>'

    html = f"""
        <tr>
            <td>{results['timestamp']}</td>
            <td><strong>{results['system']}</strong></td>
            <td>{python_ver}</td>
            <td>{results['platform']}</td>
            <td>{results['architecture']}</td>
            <td>{results['machine']}</td>
            <td>{status_badge}</td>
        </tr>"""

    return html


def main():
    """Print hello world message with environment information."""
    print("Hello, World!")
    print(f"Python version: {sys.version}")
    print(f"Platform: {platform.platform()}")
    print(f"System: {platform.system()}")

    # Gather structured results
    results = {
        "message": "Hello, World!",
        "timestamp": datetime.utcnow().isoformat(),
        "python_version": sys.version,
        "python_version_info": {
            "major": sys.version_info.major,
            "minor": sys.version_info.minor,
            "micro": sys.version_info.micro,
        },
        "platform": platform.platform(),
        "system": platform.system(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "architecture": platform.architecture()[0],
        "github_workflow": os.getenv("GITHUB_WORKFLOW", "N/A"),
        "github_run_id": os.getenv("GITHUB_RUN_ID", "N/A"),
        "github_run_number": os.getenv("GITHUB_RUN_NUMBER", "N/A"),
    }

    # Save results as JSON (for backward compatibility and processing)
    json_file = "result.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    # Generate and save HTML table row
    html_row = generate_html_row(results)
    html_file = "result.html"
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(html_row)

    print(f"\nResults saved to {json_file} and {html_file}")


if __name__ == "__main__":
    main()

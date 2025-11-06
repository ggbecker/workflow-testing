#!/usr/bin/env python3
"""Generate dynamic matrix configuration for GitHub Actions."""

import json
import sys
import os
from datetime import datetime


def generate_matrix():
    """
    Generate matrix configuration based on custom logic.

    This function can include any logic you need:
    - Date-based conditions
    - Environment variables (including PR detection)
    - External API calls
    - Configuration files
    - Conditional combinations
    """

    # Detect if running on a pull request
    is_pull_request = os.getenv("IS_PULL_REQUEST", "false") == "true"

    # Detect if running comprehensive tests (manual trigger)
    is_comprehensive = os.getenv("IS_COMPREHENSIVE", "false") == "true"

    if is_comprehensive:
        # Comprehensive: Run extensive tests with all combinations
        # Test across all platforms, including older versions, and all Python versions
        matrix = {
            "os": [
                "ubuntu-latest",
                "ubuntu-20.04",
                "windows-latest",
                "windows-2019",
                "macos-latest",
                "macos-12"
            ],
            "python-version": ["3.8", "3.9", "3.10", "3.11", "3.12"]
        }
        print(f"Generating comprehensive matrix (extensive tests - {len(matrix['os']) * len(matrix['python-version'])} combinations)", file=sys.stderr)
    elif is_pull_request:
        # Pull Request: Run fast, minimal tests
        # Only test on Ubuntu with latest Python versions
        matrix = {
            "os": ["ubuntu-latest"],
            "python-version": ["3.11", "3.12"]
        }
        print(f"Generating PR matrix (fast tests - {len(matrix['os']) * len(matrix['python-version'])} combinations)", file=sys.stderr)
    else:
        # Push to main: Run standard comprehensive tests
        # Test across all platforms and Python versions
        matrix = {
            "os": ["ubuntu-latest", "windows-latest", "macos-latest"],
            "python-version": ["3.9", "3.10", "3.11", "3.12"]
        }
        print(f"Generating push matrix (standard tests - {len(matrix['os']) * len(matrix['python-version'])} combinations)", file=sys.stderr)

    # Alternative: Use day-based logic as fallback
    # current_day = datetime.now().weekday()
    # if current_day >= 5:  # Saturday or Sunday
    #     matrix = full_matrix
    # else:
    #     matrix = minimal_matrix

    return matrix


def main():
    """Generate and output matrix as JSON."""
    matrix = generate_matrix()

    # Output the matrix as JSON
    # GitHub Actions will capture this output
    print(json.dumps(matrix))

    # Optional: Print to stderr for debugging (won't affect the output)
    print(f"Generated matrix with {len(matrix.get('os', []))} OS and "
          f"{len(matrix.get('python-version', []))} Python versions",
          file=sys.stderr)


if __name__ == "__main__":
    main()

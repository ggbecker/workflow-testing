#!/usr/bin/env python3
"""Generate dynamic matrix configuration for GitHub Actions."""

import json
import sys
from datetime import datetime


def generate_matrix():
    """
    Generate matrix configuration based on custom logic.

    This function can include any logic you need:
    - Date-based conditions
    - Environment variables
    - External API calls
    - Configuration files
    - Conditional combinations
    """

    # Example 1: Full matrix
    full_matrix = {
        "os": ["ubuntu-latest", "windows-latest", "macos-latest"],
        "python-version": ["3.9", "3.10", "3.11", "3.12"]
    }

    # Example 2: Conditional logic based on day of week
    # On weekends, run comprehensive tests; on weekdays, run minimal tests
    current_day = datetime.now().weekday()

    if current_day >= 5:  # Saturday or Sunday
        matrix = {
            "os": ["ubuntu-latest", "windows-latest", "macos-latest"],
            "python-version": ["3.9", "3.10", "3.11", "3.12"]
        }
    else:  # Weekdays - minimal testing
        matrix = {
            "os": ["ubuntu-latest"],
            "python-version": ["3.11", "3.12"]
        }

    # Example 3: Include specific combinations
    # You can also define specific combinations instead of a cross-product
    # matrix = {
    #     "include": [
    #         {"os": "ubuntu-latest", "python-version": "3.12"},
    #         {"os": "ubuntu-latest", "python-version": "3.11"},
    #         {"os": "windows-latest", "python-version": "3.12"},
    #         {"os": "macos-latest", "python-version": "3.11"},
    #     ]
    # }

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

#!/usr/bin/env python3
"""Simple Hello World script for testing GitHub Actions."""

import sys
import platform
import json
import os
from datetime import datetime


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

    # Save results to JSON file
    output_file = "result.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to {output_file}")


if __name__ == "__main__":
    main()

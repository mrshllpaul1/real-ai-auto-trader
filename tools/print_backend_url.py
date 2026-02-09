#!/usr/bin/env python3
"""
Utility: Print configured backend URL for the app.

Reads REACT_APP_BACKEND_URL from the environment and prints it, or warns if unset.
"""

import os
import sys


def main() -> int:
    url = os.environ.get("REACT_APP_BACKEND_URL", "").strip()
    if not url:
        print("REACT_APP_BACKEND_URL is not set.")
        return 1
    print(url)
    return 0


if __name__ == "__main__":
    sys.exit(main())

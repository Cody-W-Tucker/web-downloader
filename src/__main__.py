#!/usr/bin/env python3
"""
Main entry point for running the web-downloader as a module.
This allows running the package with `python -m web-downloader` or similar.
"""

# Try relative import first
try:
    from .main import main
# Fall back to direct import
except ImportError:
    from main import main

if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
"""
DiceAutoApply - Automated Job Application Tool
Main entry point for the Flet GUI application
"""

import sys
import os

# Add the src directory to the path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.app import run_app


def main():
    """Main entry point."""
    run_app()


if __name__ == "__main__":
    main()

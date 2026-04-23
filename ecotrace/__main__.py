"""Enables ``python -m ecotrace`` invocation.

This module simply delegates to the CLI entry point so that EcoTrace
can be run as a package module in addition to the console script.
"""
from ecotrace.cli import main

if __name__ == "__main__":
    main()

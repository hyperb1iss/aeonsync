#!/usr/bin/env python3

"""Lint script for the AeonSync project."""

import subprocess
import sys


def run_lint():
    """Run linting checks on the project using ruff, pylint, and mypy."""
    print("Running linting checks...")

    # Run Ruff (primary linter)
    ruff_result = subprocess.run(
        ["uv", "run", "ruff", "check", "."],
        capture_output=True,
        text=True,
        check=False,
    )

    # Run Pylint (for checks not covered by Ruff)
    pylint_result = subprocess.run(
        ["uv", "run", "pylint", "aeonsync", "tests", "scripts"],
        capture_output=True,
        text=True,
        check=False,
    )

    # Run Mypy (type checking)
    mypy_result = subprocess.run(["uv", "run", "mypy", "aeonsync"], capture_output=True, text=True, check=False)

    # Report results
    if ruff_result.returncode != 0:
        print("Ruff issues found:")
        print(ruff_result.stdout)
    else:
        print("Ruff checks passed.")

    if pylint_result.returncode != 0:
        print("Pylint issues found:")
        print(pylint_result.stdout)
    else:
        print("Pylint checks passed.")

    if mypy_result.returncode != 0:
        print("Mypy issues found:")
        print(mypy_result.stdout)
    else:
        print("Mypy checks passed.")

    # Exit with error if any checks failed
    if ruff_result.returncode != 0 or pylint_result.returncode != 0 or mypy_result.returncode != 0:
        sys.exit(1)

    print("All linting checks passed! ✨")
    sys.exit(0)


if __name__ == "__main__":
    run_lint()

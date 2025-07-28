#!/usr/bin/env python3
"""
Test runner script for the MainWindow refactoring test suite.
Provides convenient commands to run different types of tests.
"""

import sys
import os
import argparse
import subprocess
from pathlib import Path


def run_command(command, description=""):
    """Run a command and return the result."""
    if description:
        print(f"\n{description}")
        print("=" * 50)
    
    print(f"Running: {' '.join(command)}")
    result = subprocess.run(command, capture_output=True, text=True)
    
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    
    return result.returncode


def run_unit_tests():
    """Run unit tests."""
    return run_command([
        sys.executable, "-m", "pytest",
        "tests/unit/",
        "-v",
        "--tb=short"
    ], "Running Unit Tests")


def run_integration_tests():
    """Run integration tests."""
    return run_command([
        sys.executable, "-m", "pytest", 
        "tests/integration/",
        "-v",
        "--tb=short"
    ], "Running Integration Tests")


def run_performance_tests():
    """Run performance tests."""
    return run_command([
        sys.executable, "-m", "pytest",
        "tests/performance/",
        "-v",
        "--tb=short",
        "-s"  # Don't capture output for performance tests
    ], "Running Performance Tests")


def run_all_tests():
    """Run all tests."""
    return run_command([
        sys.executable, "-m", "pytest",
        "tests/",
        "-v",
        "--tb=short"
    ], "Running All Tests")


def run_specific_test(test_pattern):
    """Run tests matching a specific pattern."""
    return run_command([
        sys.executable, "-m", "pytest",
        "-k", test_pattern,
        "-v",
        "--tb=short"
    ], f"Running Tests Matching Pattern: {test_pattern}")


def run_coverage_report():
    """Run tests with coverage reporting."""
    # First install coverage if not available
    try:
        import coverage
    except ImportError:
        print("Installing coverage package...")
        subprocess.run([sys.executable, "-m", "pip", "install", "coverage"])
    
    return run_command([
        sys.executable, "-m", "pytest",
        "tests/",
        "--cov=src",
        "--cov-report=html",
        "--cov-report=term-missing",
        "-v"
    ], "Running Tests with Coverage Report")


def lint_code():
    """Run code linting."""
    commands = [
        # Run flake8 if available
        ([sys.executable, "-m", "flake8", "src/", "tests/"], "Running Flake8 Linting"),
        # Run pylint if available  
        ([sys.executable, "-m", "pylint", "src/"], "Running Pylint Analysis"),
    ]
    
    results = []
    for command, description in commands:
        try:
            result = run_command(command, description)
            results.append(result)
        except FileNotFoundError:
            print(f"Skipping {description} - tool not installed")
            results.append(0)
    
    return max(results) if results else 0


def check_requirements():
    """Check if required packages are installed."""
    required_packages = [
        "PyQt5",
        "pytest", 
        "psutil",
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.lower().replace("-", "_"))
            print(f"✓ {package} is installed")
        except ImportError:
            print(f"✗ {package} is missing")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\nTo install missing packages, run:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    return True


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description="Test runner for MainWindow refactoring")
    parser.add_argument(
        "command",
        choices=["unit", "integration", "performance", "all", "coverage", "lint", "check"],
        help="Type of tests to run"
    )
    parser.add_argument(
        "-k", "--pattern",
        help="Run tests matching this pattern"
    )
    parser.add_argument(
        "--install-deps",
        action="store_true",
        help="Install test dependencies"
    )
    
    args = parser.parse_args()
    
    # Change to project root directory
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    # Install dependencies if requested
    if args.install_deps:
        print("Installing test dependencies...")
        subprocess.run([
            sys.executable, "-m", "pip", "install",
            "pytest", "pytest-cov", "pytest-qt", "psutil", "PyQt5"
        ])
    
    # Check requirements
    if args.command != "check" and not check_requirements():
        print("Please install missing packages before running tests.")
        return 1
    
    # Run the appropriate command
    if args.command == "unit":
        return run_unit_tests()
    elif args.command == "integration":
        return run_integration_tests()
    elif args.command == "performance":
        return run_performance_tests()
    elif args.command == "all":
        if args.pattern:
            return run_specific_test(args.pattern)
        else:
            return run_all_tests()
    elif args.command == "coverage":
        return run_coverage_report()
    elif args.command == "lint":
        return lint_code()
    elif args.command == "check":
        return 0 if check_requirements() else 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
#!/usr/bin/env python3
"""
Test runner script for CLIP.LRU
"""

import sys
import subprocess
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_tests():
    """Run all tests with coverage"""
    print("Running CLIP.LRU test suite...")
    
    # Test command with coverage
    cmd = [
        "python", "-m", "pytest",
        "tests/",
        "-v",
        "--cov=app",
        "--cov-report=html",
        "--cov-report=term-missing",
        "--cov-fail-under=80"
    ]
    
    try:
        result = subprocess.run(cmd, cwd=project_root, check=True)
        print("\n✅ All tests passed!")
        print("📊 Coverage report generated in htmlcov/index.html")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Tests failed with exit code {e.returncode}")
        return False


def run_specific_test(test_path):
    """Run a specific test file or test function"""
    print(f"Running specific test: {test_path}")
    
    cmd = [
        "python", "-m", "pytest",
        test_path,
        "-v"
    ]
    
    try:
        result = subprocess.run(cmd, cwd=project_root, check=True)
        print(f"\n✅ Test {test_path} passed!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Test {test_path} failed with exit code {e.returncode}")
        return False


def main():
    """Main function"""
    if len(sys.argv) > 1:
        # Run specific test
        test_path = sys.argv[1]
        success = run_specific_test(test_path)
    else:
        # Run all tests
        success = run_tests()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

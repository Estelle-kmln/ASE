#!/usr/bin/env python3
"""Master test runner script that runs all Python unit tests."""

import sys
import unittest
from pathlib import Path

# Add parent directory to path so imports work
sys.path.insert(0, str(Path(__file__).parent.parent))


def run_custom_tests():
    """Run tests that use custom test functions (not unittest)."""
    print("\n" + "=" * 70)
    print("  RUNNING CUSTOM TESTS")
    print("=" * 70 + "\n")

    custom_test_modules = [
        ("test_game", "Game Tests"),
        ("test_hand", "Hand Tests"),
    ]

    all_passed = True
    failed_tests = []

    for module_name, display_name in custom_test_modules:
        try:
            print(f"\n{'=' * 70}")
            print(f"  {display_name}")
            print(f"{'=' * 70}\n")

            # Import and run the module's run_all_tests function
            module = __import__(module_name, fromlist=["run_all_tests"])
            if hasattr(module, "run_all_tests"):
                module.run_all_tests()
                print(f"✓ {display_name} PASSED\n")
            else:
                print(f"⚠ {display_name}: No run_all_tests() function found\n")

        except AssertionError as e:
            print(f"\n❌ {display_name} FAILED: {e}\n")
            all_passed = False
            failed_tests.append((display_name, str(e)))
        except Exception as e:
            print(f"\n❌ {display_name} ERROR: {e}\n")
            all_passed = False
            failed_tests.append((display_name, str(e)))

    return all_passed, failed_tests


def run_unittest_tests():
    """Run tests that use unittest framework."""
    print("\n" + "=" * 70)
    print("  RUNNING UNITTEST TESTS")
    print("=" * 70 + "\n")

    unittest_modules = [
        "test_score",
        "test_profile",
        "test_view_card_collection",
        "test_view_old_matches",
    ]

    # Load all test modules
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    for module_name in unittest_modules:
        try:
            module = __import__(module_name, fromlist=[])
            tests = loader.loadTestsFromModule(module)
            suite.addTests(tests)
        except Exception as e:
            print(f"⚠ Warning: Could not load {module_name}: {e}")

    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful(), result.failures + result.errors


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("  MASTER TEST RUNNER")
    print("  Running all Python unit tests")
    print("=" * 70)

    # Run custom tests
    custom_passed, custom_failures = run_custom_tests()

    # Run unittest tests
    unittest_passed, unittest_failures = run_unittest_tests()

    # Summary
    print("\n" + "=" * 70)
    print("  TEST SUMMARY")
    print("=" * 70)

    all_passed = custom_passed and unittest_passed

    if custom_failures:
        print("\n❌ Custom Test Failures:")
        for test_name, error in custom_failures:
            print(f"   - {test_name}: {error}")

    if unittest_failures:
        print("\n❌ Unittest Failures:")
        for test, error in unittest_failures:
            print(f"   - {test}")
            print(f"     {error[:200]}...")  # Truncate long errors

    if all_passed:
        print("\n" + "=" * 70)
        print("  ✓ ALL TESTS PASSED!")
        print("=" * 70 + "\n")
        return 0
    else:
        print("\n" + "=" * 70)
        print("  ❌ SOME TESTS FAILED")
        print("=" * 70 + "\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())

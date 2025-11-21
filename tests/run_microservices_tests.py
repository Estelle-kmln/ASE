#!/usr/bin/env python3
"""
Test Runner for Microservices
Runs only the active (non-deprecated) tests
"""

import subprocess
import sys
import os

def print_section(title):
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")

def run_command(cmd, description):
    """Run a command and return success status."""
    print(f"→ {description}")
    print(f"  Command: {' '.join(cmd)}")
    print()
    
    try:
        result = subprocess.run(cmd, capture_output=False, text=True)
        success = result.returncode == 0
        if success:
            print(f"✅ {description} - PASSED\n")
        else:
            print(f"❌ {description} - FAILED (exit code: {result.returncode})\n")
        return success
    except Exception as e:
        print(f"❌ {description} - ERROR: {e}\n")
        return False

def main():
    print_section("MICROSERVICES TEST RUNNER")
    
    # Change to project root
    project_root = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(project_root)  # Go up from tests/ to project root
    os.chdir(project_root)
    
    print(f"Working directory: {os.getcwd()}\n")
    
    # Clear cache
    print("→ Clearing Python cache...")
    cache_dirs = ['tests/__pycache__', '__pycache__', '.pytest_cache']
    for cache_dir in cache_dirs:
        if os.path.exists(cache_dir):
            try:
                import shutil
                shutil.rmtree(cache_dir)
                print(f"  Cleared: {cache_dir}")
            except:
                pass
    print()
    
    results = {}
    
    # Test 1: Microservices integration tests
    print_section("1. Microservices Integration Tests")
    print("These tests verify all microservice endpoints work correctly.")
    print("Prerequisites: Docker services must be running (docker-compose up)")
    print()
    
    results['microservices'] = run_command(
        [sys.executable, 'tests/test_microservices.py'],
        "Microservices API Tests"
    )
    
    # Test 2: Profile/Auth tests
    print_section("2. Profile & Authentication Tests")
    print("These tests verify user registration, login, and profile management.")
    print()
    
    results['profile'] = run_command(
        [sys.executable, '-m', 'pytest', 'tests/test_profile.py', '-v'],
        "Profile & Auth Tests"
    )
    
    # Summary
    print_section("TEST SUMMARY")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed
    
    print(f"Total test suites: {total}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print()
    
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status} - {test_name}")
    
    print()
    
    if failed == 0:
        print("🎉 ALL TESTS PASSED!")
        print()
        return 0
    else:
        print("⚠️  SOME TESTS FAILED")
        print()
        print("Common issues:")
        print("  1. Docker services not running → Run: cd microservices && docker-compose up -d")
        print("  2. Services not healthy → Wait 30s or check: docker-compose ps")
        print("  3. Port conflicts → Ensure ports 8080, 5432, 5001-5004 are free")
        print("  4. Database not initialized → Reset: docker-compose down -v && docker-compose up -d")
        print()
        return 1

if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
Test Security Analysis GitHub Actions Integration
Validates that security analysis tools work correctly in CI/CD environment
"""

import subprocess
import sys
import os


def test_bandit():
    """Test Bandit static security analysis."""
    print("🔍 Testing Bandit...")
    
    try:
        cmd = [
            sys.executable, '-m', 'bandit', 
            '-r', '.', 
            '--confidence-level', 'medium',
            '--severity-level', 'medium', 
            '--exclude', 'tests,__pycache__,.git,venv,env,frontend/node_modules',
            '--format', 'json'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode in [0, 1]:  # 0 = no issues, 1 = issues found (both are success)
            print("   ✅ Bandit test passed")
            return True
        else:
            print(f"   ❌ Bandit test failed with code {result.returncode}")
            print(f"   Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"   ❌ Bandit test failed: {e}")
        return False


def test_pip_audit():
    """Test pip-audit dependency analysis."""
    print("🔍 Testing pip-audit...")
    
    try:
        cmd = [sys.executable, '-m', 'pip_audit', '--format=json']
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode in [0, 1]:  # 0 = no vulns, 1 = vulns found (both are success)
            print("   ✅ pip-audit test passed")
            return True
        else:
            print(f"   ❌ pip-audit test failed with code {result.returncode}")
            print(f"   Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"   ❌ pip-audit test failed: {e}")
        return False


def test_static_analysis_script():
    """Test the static analysis runner script."""
    print("🔍 Testing static analysis script...")
    
    try:
        cmd = [sys.executable, 'scripts/static_analysis.py', '--quiet']
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        # Script should complete regardless of findings (exit codes 0 or 1 both acceptable)
        if result.returncode in [0, 1]:
            print("   ✅ Static analysis script test passed")
            return True
        else:
            print(f"   ❌ Static analysis script failed with code {result.returncode}")
            print(f"   Output: {result.stdout}")
            print(f"   Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"   ❌ Static analysis script test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🚀 Testing Security Analysis GitHub Actions Compatibility")
    print("=" * 60)
    
    # Change to project root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    os.chdir(project_root)
    
    tests = [
        test_bandit,
        test_pip_audit,
        test_static_analysis_script
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"   ❌ Test {test_func.__name__} crashed: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All security analysis tests passed!")
        print("🎉 GitHub Actions security workflow should work correctly")
        return 0
    else:
        print(f"❌ {total - passed} tests failed")
        print("🔧 Please fix the issues before running in GitHub Actions")
        return 1


if __name__ == '__main__':
    sys.exit(main())
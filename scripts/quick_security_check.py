#!/usr/bin/env python3
"""
Quick Security Validation
Fast security check for development workflow integration
Runs essential security checks without full analysis
"""

import os
import sys
import subprocess
from pathlib import Path


def run_quick_bandit():
    """Run quick Bandit scan focusing on high severity issues."""
    print("🔍 Quick Bandit security scan (high severity only)...")
    
    try:
        # Run bandit with high severity only for speed
        cmd = [
            sys.executable, '-m', 'bandit', 
            '-r', 
            '.',
            '--severity-level', 'medium',  # Medium and above
            '--confidence-level', 'medium', # Medium confidence and above
            '--exclude', 'tests,__pycache__,.git,venv,env,frontend/node_modules',
            '--format', 'txt'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
        
        if result.returncode == 0:
            print("   ✅ No high-severity security issues found")
            return True
        else:
            print("   ⚠️ Potential security issues detected:")
            # Show first few lines of output
            lines = result.stdout.split('\n')[:10]
            for line in lines:
                if line.strip():
                    print(f"   {line}")
            if len(result.stdout.split('\n')) > 10:
                print("   ... (run full analysis for complete results)")
            return False
            
    except FileNotFoundError:
        print("   ❌ Bandit not installed! Run: pip install bandit")
        return False
    except Exception as e:
        print(f"   ❌ Bandit scan failed: {e}")
        return False


def run_quick_pip_audit():
    """Run quick pip-audit focusing on critical vulnerabilities."""
    print("🔍 Quick dependency vulnerability check...")
    
    try:
        # Run pip-audit for critical vulnerabilities only
        result = subprocess.run([sys.executable, '-m', 'pip_audit', '--desc'], capture_output=True, text=True, encoding='utf-8', errors='ignore')
        
        if result.returncode == 0:
            print("   ✅ No known critical vulnerabilities in dependencies")
            return True
        else:
            print("   ⚠️ Known vulnerabilities detected:")
            # Show first few lines of output
            lines = result.stdout.split('\n')[:8]
            for line in lines:
                if line.strip():
                    print(f"   {line}")
            if len(result.stdout.split('\n')) > 8:
                print("   ... (run full analysis for complete results)")
            return False
            
    except FileNotFoundError:
        print("   ❌ pip-audit not installed! Run: pip install pip-audit")
        return False
    except Exception as e:
        print(f"   ❌ pip-audit scan failed: {e}")
        return False


def check_security_config():
    """Quick check of security configuration."""
    print("🔧 Quick security configuration check...")
    
    # Check if key security files exist
    security_files = [
        'microservices/utils/input_sanitizer.py',
        'tests/security_test_runner.py',
        'scripts/check_security.py'
    ]
    
    missing_files = []
    for file_path in security_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if not missing_files:
        print("   ✅ Security configuration files present")
        return True
    else:
        print("   ⚠️ Missing security files:")
        for file_path in missing_files:
            print(f"      - {file_path}")
        return False


def main():
    """Run quick security validation."""
    print("🚀 Quick Security Validation")
    print("=" * 50)
    
    # Change to project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    os.chdir(project_root)
    
    # Run checks
    bandit_ok = run_quick_bandit()
    audit_ok = run_quick_pip_audit()  
    config_ok = check_security_config()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Quick Security Check Results:")
    
    if bandit_ok and audit_ok and config_ok:
        print("✅ PASSED - Basic security checks successful")
        print("🎉 Ready for commit/deployment!")
        return 0
    else:
        print("⚠️ NEEDS ATTENTION - Some issues found")
        print("🔧 Run full security analysis for details:")
        print("   python scripts/static_analysis.py")
        print("   python scripts/check_security.py")
        return 1


if __name__ == '__main__':
    sys.exit(main())
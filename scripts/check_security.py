#!/usr/bin/env python3
"""
Security Configuration Checker
Verifies that all security measures are properly configured
"""

import os
import sys
import re


class SecurityChecker:
    """Check security configuration across microservices."""
    
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.passed_checks = []
    
    def add_issue(self, severity, message):
        """Add a security issue."""
        if severity == 'error':
            self.issues.append(f"❌ {message}")
        elif severity == 'warning':
            self.warnings.append(f"⚠️  {message}")
        else:
            self.passed_checks.append(f"✅ {message}")
    
    def check_file_exists(self, filepath, description):
        """Check if a required file exists."""
        if os.path.exists(filepath):
            self.add_issue('pass', f"{description} exists")
            return True
        else:
            self.add_issue('error', f"{description} is missing: {filepath}")
            return False
    
    def check_import_in_file(self, filepath, import_pattern, description):
        """Check if security imports are present in files."""
        if not os.path.exists(filepath):
            return False
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                if re.search(import_pattern, content):
                    self.add_issue('pass', f"{description} imports security modules")
                    return True
                else:
                    self.add_issue('error', f"{description} missing security imports")
                    return False
        except Exception as e:
            self.add_issue('error', f"Failed to check {filepath}: {str(e)}")
            return False
    
    def check_decorator_usage(self, filepath, description):
        """Check if @require_sanitized_input decorator is used."""
        if not os.path.exists(filepath):
            return False
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Count routes that should have sanitization
                routes = re.findall(r'@app\.route\([^)]*methods=\[\'POST\'', content)
                sanitized_routes = re.findall(r'@require_sanitized_input', content)
                
                if len(sanitized_routes) > 0:
                    self.add_issue('pass', f"{description} uses input sanitization decorators")
                    if len(sanitized_routes) < len(routes):
                        self.add_issue('warning', f"{description} could use more sanitization decorators")
                else:
                    self.add_issue('warning', f"{description} should use @require_sanitized_input decorators")
                
        except Exception as e:
            self.add_issue('error', f"Failed to check decorators in {filepath}: {str(e)}")
    
    def check_sql_queries(self, filepath, description):
        """Check for parameterized queries vs string formatting."""
        if not os.path.exists(filepath):
            return False
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Look for dangerous string formatting in SQL
                dangerous_patterns = [
                    r'cursor\.execute\(f".*"',  # f-string formatting
                    r'cursor\.execute\(".*\{.*\}"',  # .format() method
                    r'cursor\.execute\(".*" \%',  # % formatting
                    r'cursor\.execute\(".*\+.*"',  # string concatenation
                ]
                
                issues_found = 0
                for pattern in dangerous_patterns:
                    matches = re.findall(pattern, content)
                    issues_found += len(matches)
                
                if issues_found == 0:
                    self.add_issue('pass', f"{description} uses parameterized queries")
                else:
                    self.add_issue('error', f"{description} has {issues_found} potentially unsafe SQL queries")
                
        except Exception as e:
            self.add_issue('error', f"Failed to check SQL queries in {filepath}: {str(e)}")
    
    def check_requirements(self):
        """Check security-related dependencies."""
        req_file = "requirements.txt"
        if not os.path.exists(req_file):
            self.add_issue('error', "requirements.txt not found")
            return
        
        try:
            with open(req_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
                security_deps = ['bcrypt', 'bleach', 'validators']
                for dep in security_deps:
                    if dep in content:
                        self.add_issue('pass', f"Security dependency {dep} is installed")
                    else:
                        self.add_issue('warning', f"Consider adding security dependency: {dep}")
        
        except Exception as e:
            self.add_issue('error', f"Failed to check requirements: {str(e)}")
    
    def run_all_checks(self):
        """Run all security checks."""
        print("🔍 Running Security Configuration Check...")
        print("=" * 60)
        
        # Check if input sanitizer exists
        sanitizer_path = "microservices/utils/input_sanitizer.py"
        self.check_file_exists(sanitizer_path, "Input sanitizer module")
        
        # Check microservice security implementations
        microservices = [
            ("microservices/auth-service/app.py", "Auth Service"),
            ("microservices/game-service/app.py", "Game Service"),
            ("microservices/card-service/app.py", "Card Service"),
            ("microservices/leaderboard-service/app.py", "Leaderboard Service")
        ]
        
        for filepath, description in microservices:
            if os.path.exists(filepath):
                # Check security imports
                self.check_import_in_file(
                    filepath, 
                    r'from input_sanitizer import.*InputSanitizer', 
                    description
                )
                
                # Check decorator usage
                self.check_decorator_usage(filepath, description)
                
                # Check SQL query safety
                self.check_sql_queries(filepath, description)
            else:
                self.add_issue('warning', f"{description} file not found: {filepath}")
        
        # Check requirements
        self.check_requirements()
        
        # Check documentation
        self.check_file_exists(
            "documentation/SECURITY_DOCUMENTATION.md", 
            "Security documentation"
        )
        
        # Check test files
        self.check_file_exists(
            "tests/test_security.py", 
            "Security test suite"
        )
    
    def print_results(self):
        """Print check results."""
        print("\n📋 Security Check Results:")
        print("=" * 60)
        
        # Print passed checks
        if self.passed_checks:
            print("\n✅ PASSED CHECKS:")
            for check in self.passed_checks:
                print(f"   {check}")
        
        # Print warnings
        if self.warnings:
            print("\n⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"   {warning}")
        
        # Print critical issues
        if self.issues:
            print("\n❌ CRITICAL ISSUES:")
            for issue in self.issues:
                print(f"   {issue}")
        
        # Summary
        print("\n" + "=" * 60)
        print(f"📊 SUMMARY:")
        print(f"   ✅ Passed: {len(self.passed_checks)}")
        print(f"   ⚠️  Warnings: {len(self.warnings)}")
        print(f"   ❌ Issues: {len(self.issues)}")
        
        if len(self.issues) == 0:
            print("\n🛡️  SECURITY STATUS: GOOD")
            print("   Your microservices have proper security measures in place.")
        elif len(self.issues) <= 2:
            print("\n🔶 SECURITY STATUS: NEEDS ATTENTION")
            print("   Some security measures need to be addressed.")
        else:
            print("\n🔴 SECURITY STATUS: CRITICAL")
            print("   Multiple security issues need immediate attention.")
        
        print("=" * 60)


def main():
    """Main function."""
    # Change to project root directory if needed
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    if os.path.exists(os.path.join(project_root, 'microservices')):
        os.chdir(project_root)
    elif os.path.exists(os.path.join(os.getcwd(), 'microservices')):
        pass  # Already in the right directory
    else:
        print("❌ Error: Could not find microservices directory")
        print("   Please run this script from the project root directory")
        return 1
    
    # Run security checks
    checker = SecurityChecker()
    checker.run_all_checks()
    checker.print_results()
    
    # Return exit code based on results
    if len(checker.issues) > 0:
        return 1
    else:
        return 0


if __name__ == '__main__':
    sys.exit(main())
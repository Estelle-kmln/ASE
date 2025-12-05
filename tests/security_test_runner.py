#!/usr/bin/env python3
"""
Automated Security Test Runner
Can be integrated into CI/CD, pre-commit hooks, or regular monitoring
"""

import sys
import os
import json
import time
from datetime import datetime

# Add utils to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'microservices', 'utils'))

try:
    from input_sanitizer import InputSanitizer
except ImportError as e:
    print("❌ CRITICAL: Cannot import security modules!")
    print(f"   Error: {e}")
    print("   Please ensure all dependencies are installed: pip install -r requirements.txt")
    sys.exit(2)

class SecurityTestRunner:
    """Comprehensive security test runner with reporting."""
    
    def __init__(self, verbose=True, save_report=False):
        self.verbose = verbose
        self.save_report = save_report
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'tests': [],
            'summary': {},
            'environment': self.get_environment_info()
        }
    
    def get_environment_info(self):
        """Get environment information for reporting."""
        return {
            'python_version': sys.version,
            'platform': sys.platform,
            'cwd': os.getcwd(),
            'test_runner': 'SecurityTestRunner v1.0'
        }
    
    def log(self, message, level='INFO'):
        """Log message with optional verbosity control."""
        if self.verbose or level == 'ERROR':
            print(message)
    
    def run_test(self, test_name, test_function, expected_exception=None):
        """Run a single test and record results."""
        start_time = time.time()
        test_result = {
            'name': test_name,
            'status': 'UNKNOWN',
            'message': '',
            'duration': 0,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            result = test_function()
            execution_time = time.time() - start_time
            test_result['duration'] = round(execution_time * 1000, 2)  # ms
            
            if expected_exception:
                # Test should have raised an exception but didn't
                test_result['status'] = 'FAIL'
                test_result['message'] = f'Expected {expected_exception.__name__} but got result: {result}'
                self.log(f"❌ {test_name}: FAILED - {test_result['message']}")
            else:
                # Test passed successfully
                test_result['status'] = 'PASS'
                test_result['message'] = f'Success: {result}'
                self.log(f"✅ {test_name}: PASSED - {result}")
                
        except Exception as e:
            execution_time = time.time() - start_time
            test_result['duration'] = round(execution_time * 1000, 2)
            
            if expected_exception and isinstance(e, expected_exception):
                # Expected exception was raised - test passed
                test_result['status'] = 'PASS'
                test_result['message'] = f'Correctly blocked: {str(e)[:100]}...'
                self.log(f"✅ {test_name}: PASSED - Blocked attack")
            else:
                # Unexpected exception - test failed
                test_result['status'] = 'FAIL'
                test_result['message'] = f'Unexpected error: {str(e)}'
                self.log(f"❌ {test_name}: FAILED - {str(e)}")
        
        self.results['tests'].append(test_result)
        return test_result['status'] == 'PASS'
    
    def run_all_tests(self):
        """Run comprehensive security test suite."""
        self.log("🔒 Running Comprehensive Security Tests...")
        self.log("=" * 60)
        
        passed = 0
        failed = 0
        
        # Test 1: Safe inputs should pass
        if self.run_test(
            "Valid Username Acceptance", 
            lambda: InputSanitizer.validate_username('testuser123')
        ):
            passed += 1
        else:
            failed += 1
        
        if self.run_test(
            "Valid Game ID Acceptance",
            lambda: InputSanitizer.validate_game_id('550e8400-e29b-41d4-a716-446655440000')
        ):
            passed += 1
        else:
            failed += 1
        
        # Test 2: SQL Injection attacks should be blocked
        if self.run_test(
            "SQL Injection Protection (Username)",
            lambda: InputSanitizer.validate_username("admin'; DROP TABLE users; --"),
            expected_exception=ValueError
        ):
            passed += 1
        else:
            failed += 1
        
        if self.run_test(
            "SQL Injection Protection (String)",
            lambda: InputSanitizer.sanitize_string("'; SELECT * FROM cards; --"),
            expected_exception=ValueError
        ):
            passed += 1
        else:
            failed += 1
        
        # Test 3: XSS attacks should be blocked
        if self.run_test(
            "XSS Protection (Script Tag)",
            lambda: InputSanitizer.sanitize_string('<script>alert("xss")</script>'),
            expected_exception=ValueError
        ):
            passed += 1
        else:
            failed += 1
        
        if self.run_test(
            "XSS Protection (JavaScript URL)",
            lambda: InputSanitizer.sanitize_string('javascript:alert("xss")'),
            expected_exception=ValueError
        ):
            passed += 1
        else:
            failed += 1
        
        # Test 4: Command injection should be blocked
        if self.run_test(
            "Command Injection Protection",
            lambda: InputSanitizer.sanitize_string('; rm -rf /'),
            expected_exception=ValueError
        ):
            passed += 1
        else:
            failed += 1
        
        if self.run_test(
            "Path Traversal Protection",
            lambda: InputSanitizer.validate_game_id('../../etc/passwd'),
            expected_exception=ValueError
        ):
            passed += 1
        else:
            failed += 1
        
        # Test 5: Input bounds checking
        if self.run_test(
            "Integer Bounds Checking",
            lambda: InputSanitizer.validate_integer('999999', min_val=0, max_val=100),
            expected_exception=ValueError
        ):
            passed += 1
        else:
            failed += 1
        
        # Test 6: Card type validation
        if self.run_test(
            "Card Type Validation (Valid)",
            lambda: InputSanitizer.validate_card_type('rock')
        ):
            passed += 1
        else:
            failed += 1
        
        if self.run_test(
            "Card Type Validation (Invalid)",
            lambda: InputSanitizer.validate_card_type('invalid_type'),
            expected_exception=ValueError
        ):
            passed += 1
        else:
            failed += 1
        
        # Store summary
        self.results['summary'] = {
            'total_tests': passed + failed,
            'passed': passed,
            'failed': failed,
            'success_rate': round((passed / (passed + failed)) * 100, 1) if (passed + failed) > 0 else 0
        }
        
        # Print results
        self.log("=" * 60)
        self.log("🛡️  Security Test Results:")
        self.log(f"   ✅ Passed: {passed}")
        self.log(f"   ❌ Failed: {failed}")
        self.log(f"   📊 Success Rate: {self.results['summary']['success_rate']}%")
        
        if failed == 0:
            self.log("🎉 ALL SECURITY TESTS PASSED!")
            self.log("   Your application is protected against common injection attacks.")
            return 0
        else:
            self.log("⚠️  SOME SECURITY TESTS FAILED!")
            self.log("   Please review the input sanitization implementation.")
            return 1
    
    def save_report_file(self, filename='security_test_report.json'):
        """Save detailed test report to file."""
        if self.save_report:
            try:
                with open(filename, 'w') as f:
                    json.dump(self.results, f, indent=2)
                self.log(f"📄 Test report saved to: {filename}")
            except Exception as e:
                self.log(f"❌ Failed to save report: {e}")

def main():
    """Main function with command line argument support."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run security tests for input sanitization')
    parser.add_argument('--quiet', '-q', action='store_true', help='Reduce output verbosity')
    parser.add_argument('--save-report', '-s', action='store_true', help='Save detailed JSON report')
    parser.add_argument('--ci', action='store_true', help='CI mode: minimal output, proper exit codes')
    
    args = parser.parse_args()
    
    # Configure runner based on arguments
    verbose = not (args.quiet or args.ci)
    
    runner = SecurityTestRunner(verbose=verbose, save_report=args.save_report)
    exit_code = runner.run_all_tests()
    
    if args.save_report:
        runner.save_report_file()
    
    if args.ci:
        # CI mode: just report final status
        if exit_code == 0:
            print("SECURITY_TESTS=PASSED")
        else:
            print("SECURITY_TESTS=FAILED")
    
    return exit_code

if __name__ == '__main__':
    sys.exit(main())
#!/usr/bin/env python3
"""
Static Security Analysis Runner
Runs Bandit static analysis and pip-audit dependency analysis
Integrates with CI/CD pipelines and development workflow
"""

import os
import sys
import subprocess
import json
import time
from datetime import datetime
from pathlib import Path


class StaticAnalysisRunner:
    """Run static security analysis with Bandit and dependency analysis with pip-audit."""
    
    def __init__(self, verbose=True, save_reports=False):
        self.verbose = verbose
        self.save_reports = save_reports
        self.results = {
            'bandit': {'passed': False, 'issues': 0, 'report': None},
            'pip_audit': {'passed': False, 'vulnerabilities': 0, 'report': None},
            'summary': {'success': False, 'timestamp': datetime.now().isoformat()}
        }
        
        # Project root directory
        self.project_root = Path(__file__).parent.parent
        os.chdir(self.project_root)
    
    def log(self, message):
        """Log message if verbose."""
        if self.verbose:
            print(message)
    
    def run_bandit_analysis(self):
        """Run Bandit static security analysis."""
        self.log("🔍 Running Bandit static security analysis...")
        
        try:
            # Run bandit on the codebase
            cmd = [
                sys.executable, '-m', 'bandit', 
                '-r', 
                '.',  # Scan recursively from project root
                '-f', 'json',  # JSON output for parsing
                '--confidence-level', 'low',  # Low confidence level
                '--severity-level', 'low',   # Low severity level
                '--exclude', 'tests,__pycache__,.git,venv,env,frontend/node_modules'
            ]
            
            if self.save_reports:
                # Also generate text report for human readability
                text_cmd = cmd.copy()
                text_cmd[5] = 'txt'  # Change format to txt (adjusted index due to sys.executable and -m)
                with open('bandit_report.txt', 'w', encoding='utf-8') as f:
                    subprocess.run(text_cmd, stdout=f, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='ignore', timeout=300)
            
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore', timeout=300)
            
            if result.returncode == 0:
                self.log("   ✅ Bandit analysis completed - No security issues found")
                self.results['bandit']['passed'] = True
                self.results['bandit']['issues'] = 0
                self.results['bandit']['report'] = "No issues found"
            else:
                # Parse JSON output to count issues
                try:
                    output = json.loads(result.stdout)
                    issues = output.get('results', [])
                    self.results['bandit']['issues'] = len(issues)
                    
                    if len(issues) == 0:
                        self.log("   ✅ Bandit analysis completed - No security issues found")
                        self.results['bandit']['passed'] = True
                    else:
                        self.log(f"   ⚠️  Bandit found {len(issues)} potential security issues")
                        
                        # Show top issues if verbose
                        if self.verbose and len(issues) > 0:
                            self.log("   📋 Top security issues found:")
                            for i, issue in enumerate(issues[:5]):  # Show first 5 issues
                                severity = issue.get('issue_severity', 'UNKNOWN')
                                confidence = issue.get('issue_confidence', 'UNKNOWN')
                                test_id = issue.get('test_id', 'UNKNOWN')
                                filename = issue.get('filename', 'Unknown file')
                                line = issue.get('line_number', 'Unknown line')
                                message = issue.get('issue_text', 'No description')
                                
                                self.log(f"      {i+1}. [{severity}/{confidence}] {test_id}: {message}")
                                self.log(f"         File: {filename}:{line}")
                            
                            if len(issues) > 5:
                                self.log(f"      ... and {len(issues) - 5} more issues")
                    
                    self.results['bandit']['report'] = output
                    
                except json.JSONDecodeError:
                    self.log("   ❌ Failed to parse Bandit output")
                    self.log(f"   Raw output: {result.stdout}")
                    self.results['bandit']['report'] = result.stdout
            
            if self.save_reports and result.stdout:
                with open('bandit_report.json', 'w') as f:
                    f.write(result.stdout)
                    
        except FileNotFoundError:
            self.log("   ❌ Bandit not found! Please install: pip install bandit")
            return False
        except Exception as e:
            self.log(f"   ❌ Bandit analysis failed: {str(e)}")
            return False
        
        return self.results['bandit']['passed']
    
    def run_pip_audit(self):
        """Run pip-audit dependency vulnerability analysis."""
        self.log("🔍 Running pip-audit dependency vulnerability analysis...")
        
        try:
            # Run pip-audit on installed packages
            cmd = [sys.executable, '-m', 'pip_audit', '--format=json', '--desc']
            
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore', timeout=300)
            
            if result.returncode == 0:
                # Parse JSON output
                try:
                    if result.stdout.strip():
                        output = json.loads(result.stdout)
                        vulnerabilities = output.get('dependencies', [])
                    else:
                        vulnerabilities = []
                    
                    if len(vulnerabilities) == 0:
                        self.log("   ✅ pip-audit completed - No known vulnerabilities found")
                        self.results['pip_audit']['passed'] = True
                        self.results['pip_audit']['vulnerabilities'] = 0
                    else:
                        vuln_count = sum(len(dep.get('vulnerabilities', [])) for dep in vulnerabilities)
                        self.results['pip_audit']['vulnerabilities'] = vuln_count
                        
                        if vuln_count == 0:
                            self.log("   ✅ pip-audit completed - No known vulnerabilities found")
                            self.results['pip_audit']['passed'] = True
                        else:
                            self.log(f"   ⚠️  pip-audit found {vuln_count} known vulnerabilities")
                            
                            # Show vulnerability details if verbose
                            if self.verbose:
                                self.log("   📋 Vulnerabilities found:")
                                for dep in vulnerabilities:
                                    dep_name = dep.get('name', 'Unknown package')
                                    dep_version = dep.get('version', 'Unknown version')
                                    vulns = dep.get('vulnerabilities', [])
                                    
                                    if vulns:
                                        self.log(f"      📦 {dep_name} ({dep_version}):")
                                        for vuln in vulns[:3]:  # Show first 3 vulnerabilities per package
                                            vuln_id = vuln.get('id', 'Unknown ID')
                                            description = vuln.get('description', 'No description')[:100]
                                            fixed_in = vuln.get('fix_versions', [])
                                            
                                            self.log(f"         🔴 {vuln_id}: {description}...")
                                            if fixed_in:
                                                self.log(f"            Fix available in: {', '.join(fixed_in[:3])}")
                    
                    self.results['pip_audit']['report'] = output if result.stdout.strip() else {"dependencies": []}
                    
                except json.JSONDecodeError:
                    self.log("   ❌ Failed to parse pip-audit output")
                    self.log(f"   Raw output: {result.stdout}")
                    self.results['pip_audit']['report'] = result.stdout
                    
            else:
                # pip-audit returns non-zero when vulnerabilities are found, which is expected
                if result.stdout.strip():
                    try:
                        output = json.loads(result.stdout)
                        vulnerabilities = output.get('dependencies', [])
                        vuln_count = sum(len(dep.get('vulnerabilities', [])) for dep in vulnerabilities)
                        self.results['pip_audit']['vulnerabilities'] = vuln_count
                        
                        if vuln_count > 0:
                            self.log(f"   ⚠️  pip-audit found {vuln_count} known vulnerabilities")
                            
                            # Show vulnerability details if verbose
                            if self.verbose:
                                self.log("   📋 Vulnerabilities found:")
                                for dep in vulnerabilities:
                                    dep_name = dep.get('name', 'Unknown package')
                                    dep_version = dep.get('version', 'Unknown version')
                                    vulns = dep.get('vulnerabilities', [])
                                    
                                    if vulns:
                                        self.log(f"      📦 {dep_name} ({dep_version}):")
                                        for vuln in vulns[:3]:  # Show first 3 vulnerabilities per package
                                            vuln_id = vuln.get('id', 'Unknown ID')
                                            description = vuln.get('description', 'No description')[:100]
                                            fixed_in = vuln.get('fix_versions', [])
                                            
                                            self.log(f"         🔴 {vuln_id}: {description}...")
                                            if fixed_in:
                                                self.log(f"            Fix available in: {', '.join(fixed_in[:3])}")
                        
                        self.results['pip_audit']['report'] = output
                        
                    except json.JSONDecodeError:
                        self.log("   ❌ Failed to parse pip-audit output")
                        self.log(f"   Raw output: {result.stdout}")
                        self.results['pip_audit']['report'] = result.stdout
                else:
                    self.log(f"   ❌ pip-audit failed with exit code {result.returncode}")
                    if result.stderr:
                        self.log(f"   Error: {result.stderr}")
                    self.results['pip_audit']['report'] = {"error": result.stderr}
            
            if self.save_reports and result.stdout:
                with open('pip_audit_report.json', 'w') as f:
                    f.write(result.stdout)
                    
            # Also generate text report for readability
            if self.save_reports:
                try:
                    text_result = subprocess.run([sys.executable, '-m', 'pip_audit', '--desc'], capture_output=True, text=True, encoding='utf-8', errors='ignore')
                    with open('pip_audit_report.txt', 'w', encoding='utf-8') as f:
                        f.write(text_result.stdout)
                except:
                    pass  # Ignore errors for text report
                    
        except FileNotFoundError:
            self.log("   ❌ pip-audit not found! Please install: pip install pip-audit")
            return False
        except Exception as e:
            self.log(f"   ❌ pip-audit analysis failed: {str(e)}")
            return False
        
        return self.results['pip_audit']['passed']
    
    def run_docker_security_scan(self):
        """Check Docker images for vulnerabilities using docker scout (if available)."""
        if not self.verbose:
            return True  # Skip Docker scanning in CI mode for speed
            
        self.log("🔍 Checking for Docker security scanning capabilities...")
        
        try:
            # Check if docker scout is available
            result = subprocess.run(['docker', 'scout', 'version'], 
                                  capture_output=True, text=True, encoding='utf-8', errors='ignore')
            
            if result.returncode == 0:
                self.log("   ✅ Docker Scout available for image vulnerability scanning")
                self.log("   💡 Run 'docker scout cves <image>' to scan specific images")
            else:
                self.log("   ℹ️  Docker Scout not available - consider installing for image scanning")
                
        except FileNotFoundError:
            self.log("   ℹ️  Docker not found - skipping Docker security checks")
        except Exception as e:
            self.log(f"   ℹ️  Docker security check skipped: {str(e)}")
        
        return True
    
    def generate_security_summary(self):
        """Generate a security analysis summary."""
        bandit_passed = self.results['bandit']['passed']
        pip_audit_passed = self.results['pip_audit']['passed']
        
        self.results['summary']['success'] = bandit_passed and pip_audit_passed
        
        self.log("\n" + "=" * 70)
        self.log("🛡️  STATIC SECURITY ANALYSIS RESULTS")
        self.log("=" * 70)
        
        # Bandit results
        self.log(f"📊 Static Code Analysis (Bandit):")
        if bandit_passed:
            self.log(f"   ✅ PASSED - No security issues detected")
        else:
            issues = self.results['bandit']['issues']
            self.log(f"   ⚠️  ATTENTION NEEDED - {issues} potential issues found")
        
        # pip-audit results  
        self.log(f"📊 Dependency Vulnerability Analysis (pip-audit):")
        if pip_audit_passed:
            self.log(f"   ✅ PASSED - No known vulnerabilities in dependencies")
        else:
            vulns = self.results['pip_audit']['vulnerabilities']
            self.log(f"   ⚠️  ATTENTION NEEDED - {vulns} known vulnerabilities found")
        
        # Overall status
        self.log(f"\n🎯 OVERALL SECURITY STATUS:")
        if self.results['summary']['success']:
            self.log("   ✅ EXCELLENT - All security checks passed")
            self.log("   🎉 Your codebase passes automatic static and dependency analysis!")
        else:
            self.log("   ⚠️  NEEDS ATTENTION - Some security issues found")
            self.log("   🔧 Please review and address the identified issues")
        
        # Recommendations
        self.log(f"\n💡 RECOMMENDATIONS:")
        self.log("   • Run security analysis regularly (before commits/deployments)")
        self.log("   • Keep dependencies updated to latest secure versions")
        self.log("   • Review Bandit issues and fix high/medium severity items")
        self.log("   • Consider adding pre-commit hooks for automatic scanning")
        
        self.log("=" * 70)
        
        return self.results['summary']['success']
    
    def save_report_file(self):
        """Save comprehensive JSON report."""
        if not self.save_reports:
            return
            
        report_file = f"security_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        self.log(f"📄 Detailed report saved: {report_file}")
    
    def run_all_analysis(self):
        """Run comprehensive security analysis."""
        self.log("🚀 Starting Automatic Static and Dependency Security Analysis...")
        self.log("=" * 70)
        
        # Run static analysis
        bandit_success = self.run_bandit_analysis()
        
        # Run dependency analysis  
        pip_audit_success = self.run_pip_audit()
        
        # Optional Docker security check
        self.run_docker_security_scan()
        
        # Generate summary
        overall_success = self.generate_security_summary()
        
        # Save reports if requested
        if self.save_reports:
            self.save_report_file()
        
        return 0 if overall_success else 1


def main():
    """Main function with command line argument support."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run automatic static and dependency security analysis')
    parser.add_argument('--quiet', '-q', action='store_true', 
                       help='Reduce output verbosity')
    parser.add_argument('--save-reports', '-s', action='store_true', 
                       help='Save detailed reports to files')
    parser.add_argument('--ci', action='store_true', 
                       help='CI mode: minimal output, proper exit codes')
    
    args = parser.parse_args()
    
    # Configure runner based on arguments
    verbose = not (args.quiet or args.ci)
    save_reports = args.save_reports or args.ci
    
    runner = StaticAnalysisRunner(verbose=verbose, save_reports=save_reports)
    exit_code = runner.run_all_analysis()
    
    if args.ci:
        # CI mode: report final status for automation
        if exit_code == 0:
            print("STATIC_ANALYSIS=PASSED")
        else:
            print("STATIC_ANALYSIS=FAILED")
    
    return exit_code


if __name__ == '__main__':
    sys.exit(main())
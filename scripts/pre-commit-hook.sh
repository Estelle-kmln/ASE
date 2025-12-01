#!/bin/bash
# Pre-commit security hook
# Automatically runs security checks before allowing commits
# Place in .git/hooks/pre-commit and make executable: chmod +x .git/hooks/pre-commit

echo "🔒 Running pre-commit security validation..."

# Change to project root directory
cd "$(git rev-parse --show-toplevel)"

# Check if Python and required tools are available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3."
    exit 1
fi

# Install security tools if not available (optional - uncomment if needed)
# echo "📦 Ensuring security tools are installed..."
# pip install bandit pip-audit > /dev/null 2>&1

# Run quick security validation
echo "🚀 Running quick security checks..."
if python3 scripts/quick_security_check.py; then
    echo "✅ Pre-commit security checks passed!"
    echo "🎉 Commit allowed to proceed."
    exit 0
else
    echo ""
    echo "❌ Pre-commit security checks failed!"
    echo "🛑 Commit blocked for security reasons."
    echo ""
    echo "💡 To fix issues:"
    echo "   1. Review security findings above"
    echo "   2. Run: python scripts/static_analysis.py"
    echo "   3. Fix identified security issues"
    echo "   4. Run: python scripts/check_security.py"
    echo "   5. Try committing again"
    echo ""
    echo "🚨 SECURITY REQUIREMENT: The codebase must pass automatic static"
    echo "   and dependency analysis before commits are allowed."
    exit 1
fi
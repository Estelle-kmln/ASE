# Pre-commit security hook for Windows
# Automatically runs security checks before allowing commits
# Place in .git/hooks/pre-commit.ps1 and configure Git to use it

Write-Host "🔒 Running pre-commit security validation..." -ForegroundColor Cyan

# Change to project root directory
$projectRoot = git rev-parse --show-toplevel
Set-Location $projectRoot

# Check if Python is available
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Python not found. Please install Python." -ForegroundColor Red
    exit 1
}

# Run quick security validation
Write-Host "🚀 Running quick security checks..." -ForegroundColor Yellow

$result = & python scripts/quick_security_check.py
$exitCode = $LASTEXITCODE

if ($exitCode -eq 0) {
    Write-Host "✅ Pre-commit security checks passed!" -ForegroundColor Green
    Write-Host "🎉 Commit allowed to proceed." -ForegroundColor Green
    exit 0
} else {
    Write-Host ""
    Write-Host "❌ Pre-commit security checks failed!" -ForegroundColor Red
    Write-Host "🛑 Commit blocked for security reasons." -ForegroundColor Red
    Write-Host ""
    Write-Host "💡 To fix issues:" -ForegroundColor Yellow
    Write-Host "   1. Review security findings above"
    Write-Host "   2. Run: python scripts/static_analysis.py"
    Write-Host "   3. Fix identified security issues"
    Write-Host "   4. Run: python scripts/check_security.py"
    Write-Host "   5. Try committing again"
    Write-Host ""
    Write-Host "🚨 SECURITY REQUIREMENT: The codebase must pass automatic static" -ForegroundColor Magenta
    Write-Host "   and dependency analysis before commits are allowed."
    exit 1
}
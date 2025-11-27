import re

SQL_INJECTION_PATTERNS = [
    r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION|SCRIPT)\b)",
    r"(--|#|\/\*|\*\/)",
    r"(\bOR\b.*=.*|\bAND\b.*=.*)",
    r"(0x[0-9a-fA-F]+)",
    r"(\bCHAR\b|\bASCII\b|\bSUBSTRING\b)"
]

test_input = "admin' OR '1'='1"
print(f"Testing input: {test_input}")

for i, pattern in enumerate(SQL_INJECTION_PATTERNS):
    match = re.search(pattern, test_input, re.IGNORECASE)
    print(f"Pattern {i}: {pattern}")
    print(f"  Match: {bool(match)}")
    if match:
        print(f"  Match groups: {match.groups()}")
    print()
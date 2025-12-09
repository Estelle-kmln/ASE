"""
Script to systematically replace all direct database connections with db_manager in game-service
"""
import re

file_path = r"c:\Users\estel\OneDrive\Advanced software engineering\project\ASE\microservices\game-service\app.py"

# Read the file
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Pattern 1: Simple pattern - conn = get_db_connection() followed by cursor = conn.cursor()
# Replace with: with unit_of_work() as cursor:
pattern1 = r'(\s+)conn = get_db_connection\(\)\s+cursor = conn\.cursor\(\)'
replacement1 = r'\1with unit_of_work() as cursor:'
content = re.sub(pattern1, replacement1, content)

# Pattern 2: With RealDictCursor
pattern2 = r'(\s+)conn = get_db_connection\(\)\s+cursor = conn\.cursor\(cursor_factory=RealDictCursor\)'
replacement2 = r'\1with unit_of_work() as cursor:'
content = re.sub(pattern2, replacement2, content)

# Pattern 3: cursor = conn.cursor() alone (where conn was already created)
pattern3 = r'(\s+)cursor = conn\.cursor\(\)'
replacement3 = r'\1# cursor context managed by unit_of_work'
content = re.sub(pattern3, replacement3, content)

# Pattern 4: cursor = conn.cursor(cursor_factory=RealDictCursor) alone
pattern4 = r'(\s+)cursor = conn\.cursor\(cursor_factory=RealDictCursor\)'
replacement4 = r'\1# cursor context managed by unit_of_work'
content = re.sub(pattern4, replacement4, content)

# Pattern 5: dict_cursor = conn.cursor(cursor_factory=RealDictCursor)
pattern5 = r'(\s+)dict_cursor = conn\.cursor\(cursor_factory=RealDictCursor\)'
replacement5 = r'\1# dict_cursor context managed by unit_of_work'
content = re.sub(pattern5, replacement5, content)

# Pattern 6: Remove conn.commit()
content = re.sub(r'\s+conn\.commit\(\)\s*\n', '\n', content)

# Pattern 7: Remove conn.close()
content = re.sub(r'\s+conn\.close\(\)\s*\n', '\n', content)

# Pattern 8: Remove cursor.close()
content = re.sub(r'\s+cursor\.close\(\)\s*\n', '\n', content)

# Pattern 9: Remove dict_cursor.close()
content = re.sub(r'\s+dict_cursor\.close\(\)\s*\n', '\n', content)

# Pattern 10: Remove history_cursor.close()
content = re.sub(r'\s+history_cursor\.close\(\)\s*\n', '\n', content)

# Write back
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Database connection patterns replaced successfully!")
print("Note: Manual review recommended for complex cases.")

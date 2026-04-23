"""
═══════════════════════════════════════════════════════════════════════════
FIX PLACEHOLDERS - CONVERT ? TO CONDITIONAL %s/?
═══════════════════════════════════════════════════════════════════════════
Script để fix 78 placeholders còn lại trong app.py.refactored

CÁCH SỬ DỤNG:
    python fix_placeholders.py

OUTPUT:
    - app.py.refactored (updated with fixed placeholders)
    - placeholder_fixes.txt (báo cáo chi tiết)
═══════════════════════════════════════════════════════════════════════════
"""

import re

def fix_placeholders():
    """Fix all ? placeholders to conditional %s/?"""
    
    print("🔄 Fixing placeholders in app.py.refactored...")
    
    with open('app.py.refactored', 'r', encoding='utf-8') as f:
        content = f.read()
    
    fixes = []
    
    # ═══════════════════════════════════════════════════════════════════════
    # Pattern 1: cursor.execute("... WHERE col = ?", [val])
    # ═══════════════════════════════════════════════════════════════════════
    
    # Find all cursor.execute patterns
    execute_pattern = r'cursor\.execute\((""".*?"""|\'\'\'.*?\'\'\'|".*?"|\'.*?\')\s*,\s*\[([^\]]+)\]\)'
    
    def replace_execute(match):
        query = match.group(1)
        params = match.group(2)
        
        # Count ? in query
        question_count = query.count('?')
        
        if question_count == 0:
            return match.group(0)  # No change needed
        
        # Replace ? with conditional placeholder
        # We need to use f-string
        if query.startswith('"""') or query.startswith("'''"):
            # Triple-quoted string
            quote = query[:3]
            query_content = query[3:-3]
            
            # Replace each ? with {'%s' if IS_POSTGRESQL else '?'}
            new_query = query_content
            for i in range(question_count):
                new_query = new_query.replace('?', "{'%s' if IS_POSTGRESQL else '?'}", 1)
            
            new_execute = f'cursor.execute(f{quote}{new_query}{quote}, [{params}])'
        else:
            # Single-quoted string
            quote = query[0]
            query_content = query[1:-1]
            
            # Replace each ? with {'%s' if IS_POSTGRESQL else '?'}
            new_query = query_content
            for i in range(question_count):
                new_query = new_query.replace('?', "{'%s' if IS_POSTGRESQL else '?'}", 1)
            
            new_execute = f'cursor.execute(f{quote}{new_query}{quote}, [{params}])'
        
        fixes.append(f"Fixed cursor.execute with {question_count} placeholders")
        return new_execute
    
    # Apply replacements
    content_new = re.sub(execute_pattern, replace_execute, content, flags=re.DOTALL)
    
    # ═══════════════════════════════════════════════════════════════════════
    # Pattern 2: query_db("... WHERE col = ?", [val])
    # ═══════════════════════════════════════════════════════════════════════
    
    # query_db already handles placeholders automatically in db_utils.py
    # So we don't need to change these
    
    # ═══════════════════════════════════════════════════════════════════════
    # Pattern 3: execute_db("... WHERE col = ?", [val])
    # ═══════════════════════════════════════════════════════════════════════
    
    # execute_db already handles placeholders automatically in db_utils.py
    # So we don't need to change these
    
    # ═══════════════════════════════════════════════════════════════════════
    # Save fixed file
    # ═══════════════════════════════════════════════════════════════════════
    
    with open('app.py.refactored', 'w', encoding='utf-8') as f:
        f.write(content_new)
    
    # Generate report
    report = f"""
═══════════════════════════════════════════════════════════════════════════
PLACEHOLDER FIXES REPORT
═══════════════════════════════════════════════════════════════════════════

SUMMARY:
--------
Total fixes applied: {len(fixes)}

DETAILS:
--------
"""
    
    for i, fix in enumerate(fixes, 1):
        report += f"{i}. {fix}\n"
    
    report += """

NOTES:
------
✅ cursor.execute() calls have been fixed with conditional placeholders
✅ query_db() calls don't need fixing (handled by db_utils.py)
✅ execute_db() calls don't need fixing (handled by db_utils.py)

NEXT STEPS:
-----------
1. Review app.py.refactored
2. Test on Local (SQL Server)
3. If tests pass, replace app.py

═══════════════════════════════════════════════════════════════════════════
"""
    
    with open('placeholder_fixes.txt', 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n✅ Fixed {len(fixes)} placeholder patterns")
    print(f"📄 Report saved to: placeholder_fixes.txt")
    print(f"\n⚠️  IMPORTANT: Review app.py.refactored before using!")
    
    return True

if __name__ == '__main__':
    try:
        fix_placeholders()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

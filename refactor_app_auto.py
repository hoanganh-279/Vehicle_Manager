"""
═══════════════════════════════════════════════════════════════════════════
AUTOMATIC REFACTOR SCRIPT FOR APP.PY - DUAL-MODE
═══════════════════════════════════════════════════════════════════════════
Script tự động refactor app.py từ SQL Server sang Dual-mode

CÁCH SỬ DỤNG:
    python refactor_app_auto.py

OUTPUT:
    - app.py.refactored (file đã refactor)
    - refactor_report.txt (báo cáo chi tiết)

⚠️  LƯU Ý: Sau khi chạy script, BẮT BUỘC phải:
    1. Review file app.py.refactored
    2. Test kỹ trên Local
    3. Mới thay thế app.py chính
═══════════════════════════════════════════════════════════════════════════
"""

import re
import os
from datetime import datetime

def refactor_app_py():
    """Main refactor function"""
    
    print("🔄 Bắt đầu refactor app.py...")
    
    # Read original file
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_lines = len(content.split('\n'))
    changes = []
    
    # ═══════════════════════════════════════════════════════════════════════
    # STEP 1: Update imports
    # ═══════════════════════════════════════════════════════════════════════
    print("📝 Step 1: Updating imports...")
    
    # Remove old pyodbc import (keep it commented for reference)
    old_import = "import pyodbc"
    if old_import in content:
        content = content.replace(
            old_import,
            "# import pyodbc  # ✅ Replaced by db_utils (dual-mode)"
        )
        changes.append("✅ Commented out 'import pyodbc'")
    
    # Add new imports after load_dotenv()
    import_section = """from momo import create_momo_payment, verify_momo_ipn

# Load biến môi trường từ file .env
load_dotenv()"""
    
    new_import_section = """from momo import create_momo_payment, verify_momo_ipn

# Load biến môi trường từ file .env
load_dotenv()

# ═══════════════════════════════════════════════════════════════════════════
# DUAL-MODE DATABASE UTILITIES
# ═══════════════════════════════════════════════════════════════════════════
from db_utils import (
    get_db,
    query_db,
    execute_db,
    transaction,
    sql_limit,
    sql_limit_clause,
    sql_now,
    sql_isnull,
    sql_lock_row,
    IS_POSTGRESQL,
    init_db,
    close_db,
    return_pg_connection
)

# ✅ Dual-mode webhook
from fix_payment_webhook_dual import payment_result_route"""
    
    if import_section in content:
        content = content.replace(import_section, new_import_section)
        changes.append("✅ Added dual-mode imports")
    
    # ═══════════════════════════════════════════════════════════════════════
    # STEP 2: Comment out old database functions
    # ═══════════════════════════════════════════════════════════════════════
    print("📝 Step 2: Commenting out old database functions...")
    
    # Find and comment out get_db() function
    get_db_pattern = r'(def get_db\(\):.*?return conn)'
    match = re.search(get_db_pattern, content, re.DOTALL)
    if match:
        old_func = match.group(0)
        commented = "# ✅ get_db() now imported from db_utils.py (dual-mode)\n# " + old_func.replace('\n', '\n# ')
        content = content.replace(old_func, commented)
        changes.append("✅ Commented out old get_db() function")
    
    # Find and comment out query_db() function
    query_db_pattern = r'(def query_db\(query.*?return.*?\n)'
    match = re.search(query_db_pattern, content, re.DOTALL)
    if match:
        old_func = match.group(0)
        # Only comment if it's the simple version (not the one with transaction support)
        if 'one=False' in old_func and len(old_func) < 500:
            commented = "# ✅ query_db() now imported from db_utils.py (dual-mode)\n# " + old_func.replace('\n', '\n# ')
            content = content.replace(old_func, commented)
            changes.append("✅ Commented out old query_db() function")
    
    # Find and comment out execute_db() function (keep execute_transaction)
    execute_db_pattern = r'(def execute_db\(query, args=\(\), conn=None\):.*?finally:.*?conn\.close\(\))'
    match = re.search(execute_db_pattern, content, re.DOTALL)
    if match:
        old_func = match.group(0)
        commented = "# ✅ execute_db() now imported from db_utils.py (dual-mode)\n# " + old_func.replace('\n', '\n# ')
        content = content.replace(old_func, commented)
        changes.append("✅ Commented out old execute_db() function")
    
    # ═══════════════════════════════════════════════════════════════════════
    # STEP 3: Replace SELECT TOP N queries
    # ═══════════════════════════════════════════════════════════════════════
    print("📝 Step 3: Replacing SELECT TOP N queries...")
    
    # Pattern: SELECT TOP N
    top_pattern = r'SELECT\s+TOP\s+(\d+)'
    matches = re.findall(top_pattern, content, re.IGNORECASE)
    
    for n in set(matches):
        # Replace with f-string
        old = f'SELECT TOP {n}'
        new = f'SELECT {{sql_limit({n})}}'
        content = content.replace(old, new)
        content = content.replace(old.upper(), new)
        content = content.replace(old.lower(), new)
    
    if matches:
        changes.append(f"✅ Replaced {len(set(matches))} SELECT TOP N patterns")
    
    # Add LIMIT clause at end of queries (this is tricky, needs manual review)
    # We'll add a comment for manual review
    content = content.replace(
        'SELECT {sql_limit(',
        'SELECT {sql_limit(  # ⚠️  MANUAL: Add {sql_limit_clause(N)} at end of query\n'
    )
    
    # ═══════════════════════════════════════════════════════════════════════
    # STEP 4: Replace GETDATE()
    # ═══════════════════════════════════════════════════════════════════════
    print("📝 Step 4: Replacing GETDATE()...")
    
    getdate_count = content.count('GETDATE()')
    content = content.replace('GETDATE()', '{sql_now()}')
    
    if getdate_count > 0:
        changes.append(f"✅ Replaced {getdate_count} GETDATE() calls")
    
    # ═══════════════════════════════════════════════════════════════════════
    # STEP 5: Replace WITH (UPDLOCK, ROWLOCK)
    # ═══════════════════════════════════════════════════════════════════════
    print("📝 Step 5: Replacing row locking syntax...")
    
    lock_pattern = r'WITH\s*\(UPDLOCK,\s*ROWLOCK\)'
    lock_count = len(re.findall(lock_pattern, content, re.IGNORECASE))
    content = re.sub(lock_pattern, '{sql_lock_row()}', content, flags=re.IGNORECASE)
    
    if lock_count > 0:
        changes.append(f"✅ Replaced {lock_count} row locking patterns")
    
    # ═══════════════════════════════════════════════════════════════════════
    # STEP 6: Replace ISNULL()
    # ═══════════════════════════════════════════════════════════════════════
    print("📝 Step 6: Replacing ISNULL()...")
    
    # Pattern: ISNULL(column, default)
    isnull_pattern = r'ISNULL\(([^,]+),\s*([^)]+)\)'
    isnull_matches = re.findall(isnull_pattern, content, re.IGNORECASE)
    
    for col, default in isnull_matches:
        old = f'ISNULL({col}, {default})'
        new = f'{{sql_isnull("{col.strip()}", {default.strip()})}}'
        content = content.replace(old, new)
        content = content.replace(old.upper(), new)
        content = content.replace(old.lower(), new)
    
    if isnull_matches:
        changes.append(f"✅ Replaced {len(isnull_matches)} ISNULL() calls")
    
    # ═══════════════════════════════════════════════════════════════════════
    # STEP 7: Add placeholders warning
    # ═══════════════════════════════════════════════════════════════════════
    print("📝 Step 7: Adding placeholder warnings...")
    
    # Count ? placeholders
    placeholder_count = content.count('?')
    
    if placeholder_count > 0:
        warning = f"""
# ═══════════════════════════════════════════════════════════════════════════
# ⚠️  MANUAL REVIEW REQUIRED: PLACEHOLDERS
# ═══════════════════════════════════════════════════════════════════════════
# Found {placeholder_count} '?' placeholders in queries
# 
# ACTION REQUIRED:
# Replace all '?' with conditional placeholders:
#   cursor.execute(f"SELECT * FROM table WHERE id = {{'%s' if IS_POSTGRESQL else '?'}}", [id])
# 
# Or use query_db() / execute_db() from db_utils which handles this automatically
# ═══════════════════════════════════════════════════════════════════════════
"""
        # Add warning after imports
        content = content.replace(
            'from fix_payment_webhook_dual import payment_result_route',
            'from fix_payment_webhook_dual import payment_result_route' + warning
        )
        changes.append(f"⚠️  Added warning for {placeholder_count} placeholders (MANUAL REVIEW REQUIRED)")
    
    # ═══════════════════════════════════════════════════════════════════════
    # STEP 8: Update webhook route
    # ═══════════════════════════════════════════════════════════════════════
    print("📝 Step 8: Updating webhook route...")
    
    # Find and replace webhook import
    old_webhook = "from fix_payment_webhook import payment_result_route"
    if old_webhook in content:
        content = content.replace(
            old_webhook,
            "# from fix_payment_webhook import payment_result_route  # ✅ Old version\nfrom fix_payment_webhook_dual import payment_result_route  # ✅ Dual-mode version"
        )
        changes.append("✅ Updated webhook import to dual-mode version")
    
    # ═══════════════════════════════════════════════════════════════════════
    # STEP 9: Add initialization code
    # ═══════════════════════════════════════════════════════════════════════
    print("📝 Step 9: Adding initialization code...")
    
    init_code = """

# ═══════════════════════════════════════════════════════════════════════════
# APPLICATION LIFECYCLE - DUAL-MODE
# ═══════════════════════════════════════════════════════════════════════════

@app.before_first_request
def before_first_request():
    \"\"\"Initialize database connection pool (PostgreSQL)\"\"\"
    init_db()
    app.logger.info("✅ Database initialized (dual-mode)")

@app.teardown_appcontext
def teardown_db(exception=None):
    \"\"\"Cleanup database connections\"\"\"
    if exception:
        app.logger.error(f"❌ Request failed: {exception}")

# Cleanup on shutdown
import atexit
atexit.register(close_db)

"""
    
    # Add before if __name__ == '__main__':
    if "if __name__ == '__main__':" in content:
        content = content.replace(
            "if __name__ == '__main__':",
            init_code + "if __name__ == '__main__':"
        )
        changes.append("✅ Added initialization code")
    
    # ═══════════════════════════════════════════════════════════════════════
    # STEP 10: Update main block
    # ═══════════════════════════════════════════════════════════════════════
    print("📝 Step 10: Updating main block...")
    
    old_main = """if __name__ == '__main__':
    # Tạo thư mục uploads nếu chưa có
    os.makedirs(os.path.join('static', 'uploads'), exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5000)"""
    
    new_main = """if __name__ == '__main__':
    # Tạo thư mục uploads nếu chưa có
    os.makedirs(os.path.join('static', 'uploads'), exist_ok=True)
    
    # ✅ Initialize database (dual-mode)
    init_db()
    
    # Run app
    app.run(debug=True, host='0.0.0.0', port=5000)"""
    
    if old_main in content:
        content = content.replace(old_main, new_main)
        changes.append("✅ Updated main block with init_db()")
    
    # ═══════════════════════════════════════════════════════════════════════
    # Save refactored file
    # ═══════════════════════════════════════════════════════════════════════
    print("💾 Saving refactored file...")
    
    with open('app.py.refactored', 'w', encoding='utf-8') as f:
        f.write(content)
    
    refactored_lines = len(content.split('\n'))
    
    # ═══════════════════════════════════════════════════════════════════════
    # Generate report
    # ═══════════════════════════════════════════════════════════════════════
    print("📊 Generating report...")
    
    report = f"""
═══════════════════════════════════════════════════════════════════════════
REFACTOR REPORT - APP.PY TO DUAL-MODE
═══════════════════════════════════════════════════════════════════════════
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

SUMMARY:
--------
Original file: app.py ({original_lines} lines)
Refactored file: app.py.refactored ({refactored_lines} lines)
Total changes: {len(changes)}

CHANGES MADE:
-------------
"""
    
    for i, change in enumerate(changes, 1):
        report += f"{i}. {change}\n"
    
    report += """

NEXT STEPS:
-----------
1. ⚠️  REVIEW app.py.refactored carefully
2. ⚠️  MANUAL: Fix all placeholder warnings (? → %s conditional)
3. ⚠️  MANUAL: Add {sql_limit_clause(N)} at end of TOP N queries
4. ✅ Test on Local (SQL Server):
   python app.py.refactored
5. ✅ If tests pass, backup and replace:
   cp app.py app.py.backup
   cp app.py.refactored app.py
6. ✅ Test again
7. ✅ Commit and push to GitHub
8. ✅ Deploy to Render

WARNINGS:
---------
⚠️  This script handles COMMON patterns only!
⚠️  MANUAL REVIEW is REQUIRED for:
    - Placeholder conversions (? → %s)
    - Complex queries with subqueries
    - Dynamic SQL generation
    - Error handling in database operations

═══════════════════════════════════════════════════════════════════════════
"""
    
    with open('refactor_report.txt', 'w', encoding='utf-8') as f:
        f.write(report)
    
    print("\n" + "="*75)
    print("✅ REFACTOR COMPLETED!")
    print("="*75)
    print(f"\n📄 Output files:")
    print(f"   - app.py.refactored ({refactored_lines} lines)")
    print(f"   - refactor_report.txt")
    print(f"\n📊 Changes made: {len(changes)}")
    print(f"\n⚠️  NEXT: Review app.py.refactored and fix manual items!")
    print("="*75 + "\n")
    
    return True

if __name__ == '__main__':
    try:
        refactor_app_py()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

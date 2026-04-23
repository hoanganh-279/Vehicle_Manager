"""
═══════════════════════════════════════════════════════════════════════════
CONVERT TO POSTGRESQL - AUTOMATIC MIGRATION SCRIPT
═══════════════════════════════════════════════════════════════════════════
Script tự động chuyển đổi app.py từ SQL Server sang PostgreSQL

CÁCH SỬ DỤNG:
    python convert_to_postgresql.py

OUTPUT:
    - app_postgresql.py (file đã chuyển đổi)
    - conversion_report.txt (báo cáo chi tiết)
═══════════════════════════════════════════════════════════════════════════
"""

import re
from datetime import datetime

def convert_app_to_postgresql():
    """Convert app.py from SQL Server to PostgreSQL"""
    
    print("🔄 Đang chuyển đổi app.py sang PostgreSQL...")
    
    # Read original file
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    changes = []
    
    # ═══════════════════════════════════════════════════════════════════════
    # STEP 1: Replace imports
    # ═══════════════════════════════════════════════════════════════════════
    print("📝 Step 1: Replacing imports...")
    
    # Find and replace pyodbc imports
    old_imports = """import psycopg2
import stripe"""
    
    new_imports = """import stripe
from database import (
    init_connection_pool,
    create_tables,
    get_db_connection,
    get_db_cursor,
    query_db,
    execute_db,
    close_connection_pool
)"""
    
    if old_imports in content:
        content = content.replace(old_imports, new_imports)
        changes.append("✅ Replaced imports with PostgreSQL database utilities")
    
    # ═══════════════════════════════════════════════════════════════════════
    # STEP 2: Remove old database config
    # ═══════════════════════════════════════════════════════════════════════
    print("📝 Step 2: Removing old database config...")
    
    # Remove SQL Server config section
    db_config_pattern = r'# =+\n# CẤU HÌNH DATABASE.*?# =+\n.*?(?=# =+\n# CẤU HÌNH|from flask import)'
    content = re.sub(db_config_pattern, '', content, flags=re.DOTALL)
    changes.append("✅ Removed SQL Server configuration")
    
    # ═══════════════════════════════════════════════════════════════════════
    # STEP 3: Add database initialization
    # ═══════════════════════════════════════════════════════════════════════
    print("📝 Step 3: Adding database initialization...")
    
    init_code = """
# =============================================================================
# DATABASE INITIALIZATION
# =============================================================================

def initialize_database():
    \"\"\"Initialize database connection and create tables\"\"\"
    try:
        # Initialize connection pool
        init_connection_pool()
        app.logger.info("✅ Connection pool initialized")
        
        # Create tables if not exist
        create_tables()
        app.logger.info("✅ Database tables created")
        
        return True
    except Exception as e:
        app.logger.error(f"❌ Database initialization failed: {e}")
        return False

# Initialize database when app starts
with app.app_context():
    initialize_database()

"""
    
    # Add after Flask app initialization
    flask_init_pattern = r"(app\.secret_key = .*?\n)"
    content = re.sub(flask_init_pattern, r"\1" + init_code, content)
    changes.append("✅ Added database initialization code")
    
    # ═══════════════════════════════════════════════════════════════════════
    # STEP 4: Replace placeholders ? with %s
    # ═══════════════════════════════════════════════════════════════════════
    print("📝 Step 4: Replacing SQL placeholders...")
    
    # Replace ? with %s in SQL queries
    # This is a simple replacement - may need manual review
    placeholder_count = content.count('?')
    content = content.replace('?', '%s')
    changes.append(f"✅ Replaced {placeholder_count} placeholders (? → %s)")
    
    # ═══════════════════════════════════════════════════════════════════════
    # STEP 5: Update port configuration
    # ═══════════════════════════════════════════════════════════════════════
    print("📝 Step 5: Updating port configuration...")
    
    old_run = "app.run(debug=True, host='0.0.0.0', port=5000)"
    new_run = """port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)"""
    
    if old_run in content:
        content = content.replace(old_run, new_run)
        changes.append("✅ Updated port configuration for Render")
    
    # ═══════════════════════════════════════════════════════════════════════
    # STEP 6: Add cleanup on shutdown
    # ═══════════════════════════════════════════════════════════════════════
    print("📝 Step 6: Adding cleanup code...")
    
    cleanup_code = """
# Cleanup on shutdown
import atexit
atexit.register(close_connection_pool)

"""
    
    # Add before if __name__ == '__main__':
    if "if __name__ == '__main__':" in content:
        content = content.replace(
            "if __name__ == '__main__':",
            cleanup_code + "if __name__ == '__main__':"
        )
        changes.append("✅ Added cleanup code")
    
    # ═══════════════════════════════════════════════════════════════════════
    # Save converted file
    # ═══════════════════════════════════════════════════════════════════════
    print("💾 Saving converted file...")
    
    with open('app_postgresql.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    # ═══════════════════════════════════════════════════════════════════════
    # Generate report
    # ═══════════════════════════════════════════════════════════════════════
    print("📊 Generating report...")
    
    report = f"""
═══════════════════════════════════════════════════════════════════════════
CONVERSION REPORT - SQL SERVER TO POSTGRESQL
═══════════════════════════════════════════════════════════════════════════
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

SUMMARY:
--------
Original file: app.py
Converted file: app_postgresql.py
Total changes: {len(changes)}

CHANGES MADE:
-------------
"""
    
    for i, change in enumerate(changes, 1):
        report += f"{i}. {change}\n"
    
    report += """

NEXT STEPS:
-----------
1. ⚠️  REVIEW app_postgresql.py carefully
2. ⚠️  MANUAL: Check all SQL queries for PostgreSQL compatibility
3. ⚠️  MANUAL: Update card_register and card_topup routes (see guide)
4. ✅ Test locally if possible
5. ✅ Backup app.py:
   cp app.py app.py.backup
6. ✅ Replace with converted version:
   cp app_postgresql.py app.py
7. ✅ Deploy to Render following DEPLOY_RENDER_COMPLETE_GUIDE.md

IMPORTANT NOTES:
----------------
⚠️  This script handles COMMON patterns only!
⚠️  MANUAL REVIEW is REQUIRED for:
    - Complex SQL queries
    - Transaction handling
    - Error handling
    - Business logic

⚠️  MUST IMPLEMENT MANUALLY:
    - card_register route (see guide)
    - card_topup route with TRANSACTION (see guide)
    - calculate_parking_fee function (see guide)

═══════════════════════════════════════════════════════════════════════════
"""
    
    with open('conversion_report.txt', 'w', encoding='utf-8') as f:
        f.write(report)
    
    print("\n" + "="*75)
    print("✅ CONVERSION COMPLETED!")
    print("="*75)
    print(f"\n📄 Output files:")
    print(f"   - app_postgresql.py")
    print(f"   - conversion_report.txt")
    print(f"\n📊 Changes made: {len(changes)}")
    print(f"\n⚠️  NEXT: Review app_postgresql.py and implement manual changes!")
    print(f"📖 Read: DEPLOY_RENDER_COMPLETE_GUIDE.md for detailed instructions")
    print("="*75 + "\n")
    
    return True

if __name__ == '__main__':
    try:
        convert_app_to_postgresql()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

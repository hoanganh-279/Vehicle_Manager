# 🔄 HƯỚNG DẪN REFACTOR APP.PY - DUAL-MODE

## 📋 TỔNG QUAN

File `app.py` hiện tại (2153 dòng) đang sử dụng SQL Server trực tiếp. Cần refactor để hỗ trợ dual-mode (PostgreSQL + SQL Server).

## 🎯 MỤC TIÊU

- ✅ Local vẫn chạy với SQL Server (pyodbc)
- ✅ Render chạy với PostgreSQL (psycopg2)
- ✅ Không phá vỡ logic hiện tại
- ✅ Tự động nhận diện môi trường

---

## 📝 BƯỚC 1: THAY THẾ IMPORTS

### Trước (Dòng 1-20):
```python
import pyodbc
import os
from flask import Flask, render_template, request, jsonify
# ... other imports
```

### Sau:
```python
# ═══════════════════════════════════════════════════════════════════════════
# IMPORTS - DUAL-MODE SUPPORT
# ═══════════════════════════════════════════════════════════════════════════
import os
from flask import Flask, render_template, request, jsonify
# ... other imports

# ✅ Dual-mode database utilities
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
    close_db
)

# ✅ Dual-mode webhook
from fix_payment_webhook_dual import payment_result_route
```

---

## 📝 BƯỚC 2: XÓA HÀM get_db() CŨ

### Trước (Dòng ~50-70):
```python
def get_db():
    """Tạo kết nối database"""
    conn = pyodbc.connect(
        f'DRIVER={{ODBC Driver 17 for SQL Server}};'
        f'SERVER={os.getenv("DB_SERVER", r"LAPTOP-3J6T1I18\SQLEXPRESS01")};'
        f'DATABASE={os.getenv("DB_DATABASE", "ParkingManagement")};'
        f'Trusted_Connection=yes;'
    )
    conn.setdecoding(pyodbc.SQL_WCHAR, encoding='utf-16-le')
    conn.setencoding(encoding='utf-16-le')
    return conn
```

### Sau:
```python
# ✅ Đã import từ db_utils.py - XÓA HÀM NÀY
```

---

## 📝 BƯỚC 3: REFACTOR HÀM query_db()

### Trước (Dòng ~80-100):
```python
def query_db(query, args=None, one=False):
    conn = get_db()
    cursor = conn.cursor()
    if args:
        cursor.execute(query, args)
    else:
        cursor.execute(query)
    # ... rest of function
```

### Sau:
```python
# ✅ Đã import từ db_utils.py - XÓA HÀM NÀY
```

---

## 📝 BƯỚC 4: REFACTOR HÀM execute_db()

### Trước (Dòng ~110-130):
```python
def execute_db(query, args=None):
    conn = get_db()
    cursor = conn.cursor()
    # ... rest of function
```

### Sau:
```python
# ✅ Đã import từ db_utils.py - XÓA HÀM NÀY
```

---

## 📝 BƯỚC 5: REFACTOR CÁC QUERY SỬ DỤNG TOP N

### Ví dụ 1: Admin Dashboard (Dòng ~500)

#### Trước:
```python
cfg = query_db("SELECT TOP 1 * FROM parking_config", one=True) or {}
```

#### Sau:
```python
cfg = query_db(f"SELECT {sql_limit(1)} * FROM parking_config {sql_limit_clause(1)}", one=True) or {}
```

### Ví dụ 2: Recent Vehicles (Dòng ~600)

#### Trước:
```python
recent_vehicles = query_db("""
    SELECT TOP 10 * 
    FROM vehicles 
    WHERE status='parked' 
    ORDER BY entry_time DESC
""")
```

#### Sau:
```python
recent_vehicles = query_db(f"""
    SELECT {sql_limit(10)} * 
    FROM vehicles 
    WHERE status='parked' 
    ORDER BY entry_time DESC
    {sql_limit_clause(10)}
""")
```

---

## 📝 BƯỚC 6: REFACTOR GETDATE() → sql_now()

### Ví dụ 1: Insert Vehicle (Dòng ~1650)

#### Trước:
```python
vehicle_id = execute_db(
    """INSERT INTO vehicles
       (license_plate, vehicle_type, status, entry_time)
       VALUES (?, ?, 'parked', GETDATE())""",
    [license_plate, vehicle_type]
)
```

#### Sau:
```python
vehicle_id = execute_db(
    f"""INSERT INTO vehicles
       (license_plate, vehicle_type, status, entry_time)
       VALUES ({'%s, %s, %s, ' + sql_now() if IS_POSTGRESQL else '?, ?, ?, ' + sql_now()})""",
    [license_plate, vehicle_type, 'parked']
)
```

### Ví dụ 2: Update Exit Time (Dòng ~1850)

#### Trước:
```python
cursor.execute("""
    UPDATE vehicles
    SET status = 'exited',
        exit_time = GETDATE()
    WHERE id = ?
""", [vehicle_id])
```

#### Sau:
```python
cursor.execute(f"""
    UPDATE vehicles
    SET status = 'exited',
        exit_time = {sql_now()}
    WHERE id = {'%s' if IS_POSTGRESQL else '?'}
""", [vehicle_id])
```

---

## 📝 BƯỚC 7: REFACTOR ROW LOCKING

### Ví dụ: Parking Exit (Dòng ~1750-1890)

#### Trước:
```python
cursor.execute("""
    SELECT id, license_plate, vehicle_type, entry_time, status
    FROM vehicles WITH (UPDLOCK, ROWLOCK)
    WHERE id = ? AND status = 'parked'
""", [vehicle_id])
```

#### Sau:
```python
cursor.execute(f"""
    SELECT id, license_plate, vehicle_type, entry_time, status
    FROM vehicles {sql_lock_row()}
    WHERE id = {'%s' if IS_POSTGRESQL else '?'} AND status = 'parked'
""", [vehicle_id])
```

---

## 📝 BƯỚC 8: REFACTOR ISNULL() → sql_isnull()

### Ví dụ: Balance Check

#### Trước:
```python
cursor.execute("""
    SELECT id, ISNULL(balance, 0) AS balance
    FROM cards
    WHERE id = ?
""", [card_id])
```

#### Sau:
```python
cursor.execute(f"""
    SELECT id, {sql_isnull('balance', 0)} AS balance
    FROM cards
    WHERE id = {'%s' if IS_POSTGRESQL else '?'}
""", [card_id])
```

---

## 📝 BƯỚC 9: REFACTOR WEBHOOK ROUTE

### Trước (Dòng ~2000):
```python
from fix_payment_webhook import payment_result_route

@app.route('/payment/result', methods=['GET', 'POST'])
def payment_result():
    return payment_result_route()
```

### Sau:
```python
# ✅ Đã import từ fix_payment_webhook_dual.py ở đầu file

@app.route('/payment/result', methods=['GET', 'POST'])
def payment_result():
    return payment_result_route()
```

---

## 📝 BƯỚC 10: THÊM INITIALIZATION VÀ CLEANUP

### Thêm vào cuối file (Dòng ~2150):

```python
# ═══════════════════════════════════════════════════════════════════════════
# APPLICATION LIFECYCLE
# ═══════════════════════════════════════════════════════════════════════════

@app.before_first_request
def before_first_request():
    """Initialize database connection pool (PostgreSQL)"""
    init_db()
    app.logger.info("✅ Database initialized")

@app.teardown_appcontext
def teardown_db(exception=None):
    """Cleanup database connections"""
    if exception:
        app.logger.error(f"❌ Request failed: {exception}")

# Cleanup on shutdown
import atexit
atexit.register(close_db)

# ═══════════════════════════════════════════════════════════════════════════
# RUN APPLICATION
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    # Tạo thư mục uploads nếu chưa có
    os.makedirs(os.path.join('static', 'uploads'), exist_ok=True)
    
    # Initialize database
    init_db()
    
    # Run app
    app.run(debug=True, host='0.0.0.0', port=5000)
```

---

## 📝 BƯỚC 11: REFACTOR CARD TOPUP ROUTE

### Trước (Dòng ~1916-1930):
```python
@app.route('/card/topup', methods=['GET', 'POST'])
def card_topup():
    if request.method == 'POST':
        # ... existing code
        
        conn = get_db()
        cursor = conn.cursor()
        
        try:
            # ✅ LOCK card để tránh race condition
            cursor.execute("""
                SELECT id, balance
                FROM cards WITH (UPDLOCK, ROWLOCK)
                WHERE id = ?
            """, [card_id])
            
            # ... rest of code
```

### Sau:
```python
@app.route('/card/topup', methods=['GET', 'POST'])
def card_topup():
    if request.method == 'POST':
        # ... existing code
        
        conn = get_db()
        cursor = conn.cursor()
        
        try:
            # ✅ LOCK card để tránh race condition (Dual-mode)
            cursor.execute(f"""
                SELECT id, balance
                FROM cards {sql_lock_row()}
                WHERE id = {'%s' if IS_POSTGRESQL else '?'}
            """, [card_id])
            
            # ... rest of code (cũng cần refactor GETDATE() và placeholders)
```

---

## 🔍 DANH SÁCH TẤT CẢ CHỖ CẦN SỬA

### 1. Queries sử dụng TOP N (≈15 chỗ)
- Admin dashboard: `SELECT TOP 1 * FROM parking_config`
- Recent vehicles: `SELECT TOP 10 * FROM vehicles`
- Revenue reports: `SELECT TOP 100 * FROM vehicles`

### 2. Queries sử dụng GETDATE() (≈20 chỗ)
- Insert vehicles: `entry_time = GETDATE()`
- Update exit: `exit_time = GETDATE()`
- Topup transactions: `created_at = GETDATE()`
- Balance history: `created_at = GETDATE()`

### 3. Queries sử dụng WITH (UPDLOCK, ROWLOCK) (≈5 chỗ)
- Parking exit: Lock vehicle row
- Card topup: Lock card row
- Webhook: Lock transaction rows

### 4. Queries sử dụng ISNULL() (≈8 chỗ)
- Balance checks: `ISNULL(balance, 0)`
- Count queries: `ISNULL(COUNT(*), 0)`

### 5. Placeholders ? → %s (TẤT CẢ queries)
- SQL Server: `WHERE id = ?`
- PostgreSQL: `WHERE id = %s`

---

## 🛠️ SCRIPT TỰ ĐỘNG (KHUYẾN NGHỊ)

Tạo file `refactor_app.py`:

```python
"""
Script tự động refactor app.py từ SQL Server sang Dual-mode
"""

import re

def refactor_app_py():
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Thay thế imports
    content = re.sub(
        r'import pyodbc',
        'from db_utils import get_db, query_db, execute_db, transaction, sql_limit, sql_limit_clause, sql_now, sql_isnull, sql_lock_row, IS_POSTGRESQL, init_db, close_db',
        content
    )
    
    # 2. Xóa hàm get_db() cũ
    content = re.sub(
        r'def get_db\(\):.*?return conn',
        '# ✅ get_db() imported from db_utils.py',
        content,
        flags=re.DOTALL
    )
    
    # 3. Thay thế SELECT TOP N
    content = re.sub(
        r'SELECT TOP (\d+)',
        r'SELECT {sql_limit(\1)}',
        content
    )
    
    # 4. Thay thế GETDATE()
    content = re.sub(
        r'GETDATE\(\)',
        '{sql_now()}',
        content
    )
    
    # 5. Thay thế WITH (UPDLOCK, ROWLOCK)
    content = re.sub(
        r'WITH \(UPDLOCK, ROWLOCK\)',
        '{sql_lock_row()}',
        content
    )
    
    # 6. Thay thế ISNULL
    content = re.sub(
        r'ISNULL\(([^,]+),\s*([^)]+)\)',
        r'{sql_isnull("\1", \2)}',
        content
    )
    
    # 7. Backup file cũ
    with open('app.py.backup', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Refactored app.py saved to app.py.backup")
    print("⚠️  Vui lòng kiểm tra kỹ trước khi thay thế!")

if __name__ == '__main__':
    refactor_app_py()
```

**Chạy script:**
```bash
python refactor_app.py
```

---

## ⚠️ LƯU Ý QUAN TRỌNG

### 1. Placeholders khác nhau
- **SQL Server (pyodbc)**: Dùng `?`
- **PostgreSQL (psycopg2)**: Dùng `%s`

**Giải pháp**: Dùng f-string với điều kiện
```python
cursor.execute(f"""
    SELECT * FROM vehicles
    WHERE id = {'%s' if IS_POSTGRESQL else '?'}
""", [vehicle_id])
```

### 2. SCOPE_IDENTITY() vs RETURNING

**SQL Server:**
```python
cursor.execute("INSERT INTO vehicles (...) VALUES (...)")
cursor.execute("SELECT SCOPE_IDENTITY()")
vehicle_id = cursor.fetchone()[0]
```

**PostgreSQL:**
```python
cursor.execute("INSERT INTO vehicles (...) VALUES (...) RETURNING id")
vehicle_id = cursor.fetchone()[0]
```

**Giải pháp**: Dùng `execute_db()` từ `db_utils.py` (đã xử lý)

### 3. Transaction Management

**SQL Server**: Auto-commit mặc định  
**PostgreSQL**: Cần explicit commit

**Giải pháp**: Dùng context manager `transaction()` từ `db_utils.py`

```python
from db_utils import transaction

with transaction() as (conn, cursor):
    cursor.execute("UPDATE cards SET balance = balance + 100 WHERE id = 1")
    cursor.execute("INSERT INTO balance_history (...) VALUES (...)")
    # Auto-commit on success, auto-rollback on exception
```

---

## ✅ CHECKLIST REFACTOR

- [ ] Backup `app.py` → `app.py.backup`
- [ ] Thay thế imports
- [ ] Xóa hàm `get_db()`, `query_db()`, `execute_db()` cũ
- [ ] Refactor tất cả `SELECT TOP N`
- [ ] Refactor tất cả `GETDATE()`
- [ ] Refactor tất cả `WITH (UPDLOCK, ROWLOCK)`
- [ ] Refactor tất cả `ISNULL()`
- [ ] Refactor placeholders `?` → conditional `%s/?`
- [ ] Thêm `init_db()` và `close_db()`
- [ ] Test trên Local (SQL Server)
- [ ] Test trên Render (PostgreSQL)

---

## 🧪 TESTING

### Test Local (SQL Server)
```bash
# Không có DATABASE_URL → Dùng SQL Server
python app.py

# Kiểm tra logs
# 🗄️  Using SQL Server (Local)
```

### Test Render (PostgreSQL)
```bash
# Set DATABASE_URL
export DATABASE_URL="postgresql://user:pass@host/db"

# Chạy app
python app.py

# Kiểm tra logs
# 🐘 Using PostgreSQL (Render)
```

---

## 📚 TÀI LIỆU THAM KHẢO

- [db_utils.py](./db_utils.py) - Dual-mode database utilities
- [fix_payment_webhook_dual.py](./fix_payment_webhook_dual.py) - Dual-mode webhook
- [schema_postgresql.sql](./schema_postgresql.sql) - PostgreSQL schema
- [HUONG_DAN_DEPLOY_RENDER.md](./HUONG_DAN_DEPLOY_RENDER.md) - Deployment guide

---

**Tác giả**: KIRO AI Assistant  
**Ngày tạo**: 2026-04-21  
**Phiên bản**: 1.0.0

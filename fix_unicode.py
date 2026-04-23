"""
fix_unicode.py — Fix dữ liệu UTF-8 bị lưu sai vào NVARCHAR SQL Server
Root cause: dữ liệu được insert bằng sqlcmd không set encoding,
nên UTF-8 bytes của tiếng Việt bị lưu như Latin-1 chars vào NVARCHAR.

Giải pháp: đọc raw bytes, decode đúng, ghi lại.
"""
import pyodbc

def get_conn():
    conn = pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};'
        'SERVER=LAPTOP-3J6T1I18\\SQLEXPRESS01;'
        'DATABASE=ParkingManagement;'
        'Trusted_Connection=yes;'
    )
    # Đọc NVARCHAR như UTF-16LE (đúng)
    conn.setdecoding(pyodbc.SQL_WCHAR, encoding='utf-16-le')
    # Ghi string Python như UTF-16LE vào NVARCHAR
    conn.setencoding(encoding='utf-16-le')
    return conn

def fix_column(table, col, id_col='id'):
    """Fix một cột bị lỗi encoding trong một bảng."""
    conn = get_conn()
    cur = conn.cursor()
    
    # Đọc raw bytes của cột
    cur.execute(f"SELECT {id_col}, CONVERT(VARBINARY(MAX), {col}) FROM {table}")
    rows = cur.fetchall()
    
    fixed = 0
    for row in rows:
        row_id, raw = row
        if not raw:
            continue
        
        # Decode UTF-16LE (cách SQL Server lưu NVARCHAR)
        try:
            current_str = raw.decode('utf-16-le')
        except Exception:
            continue
        
        # Thử decode lại: nếu string chứa ký tự Latin-1 mà thực ra là UTF-8
        # Encode lại thành Latin-1 bytes rồi decode UTF-8
        try:
            fixed_str = current_str.encode('latin-1').decode('utf-8')
            if fixed_str != current_str:
                cur.execute(f"UPDATE {table} SET {col}=? WHERE {id_col}=?", [fixed_str, row_id])
                print(f"  Fixed {table}.{col} id={row_id}: {current_str!r} -> {fixed_str!r}")
                fixed += 1
        except (UnicodeEncodeError, UnicodeDecodeError):
            # Không thể fix theo cách này — bỏ qua
            pass
    
    conn.commit()
    conn.close()
    return fixed

print("=== Fix vehicle_type ===")
n = fix_column('vehicles', 'vehicle_type')
print(f"Fixed {n} records")

print("\n=== Fix plate_color ===")
n = fix_column('vehicles', 'plate_color')
print(f"Fixed {n} records")

print("\n=== Fix plate_type ===")
n = fix_column('vehicles', 'plate_type')
print(f"Fixed {n} records")

print("\n=== Fix cards.name ===")
n = fix_column('cards', 'name')
print(f"Fixed {n} records")

# Verify
print("\n=== Kết quả sau fix ===")
conn = get_conn()
cur = conn.cursor()
cur.execute("SELECT DISTINCT vehicle_type FROM vehicles")
print("vehicle_types:", [r[0] for r in cur.fetchall()])
cur.execute("SELECT DISTINCT plate_color FROM vehicles")
print("plate_colors:", [r[0] for r in cur.fetchall()])
cur.execute("SELECT id, name FROM cards ORDER BY created_at")
print("cards:")
for r in cur.fetchall():
    print(f"  {r[0]:20} | {r[1]}")
conn.close()

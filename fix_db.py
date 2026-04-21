"""
fix_db.py — Sửa toàn bộ lỗi dữ liệu trong DB
1. Xóa 3 record CARD-DEMO bị lỗi encoding, insert lại đúng
2. Chuẩn hóa vehicle_type: motorbike -> Xe máy, car -> Xe hơi
3. Chuẩn hóa plate_type: Thường -> Biển thường
Chạy: python fix_db.py
"""
import pyodbc

conn = pyodbc.connect(
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=LAPTOP-3J6T1I18\\SQLEXPRESS01;'
    'DATABASE=ParkingManagement;'
    'Trusted_Connection=yes;'
)
conn.setdecoding(pyodbc.SQL_CHAR,  encoding='cp1252')
conn.setdecoding(pyodbc.SQL_WCHAR, encoding='utf-16-le')
conn.setencoding(encoding='utf-16-le')
cur = conn.cursor()

# ── 1. Xóa CARD-DEMO bị lỗi encoding ──
print("1. Xóa CARD-DEMO bị lỗi encoding...")
cur.execute("DELETE FROM vehicles WHERE card_id LIKE 'CARD-DEMO%'")
cur.execute("DELETE FROM topup_transactions WHERE card_id LIKE 'CARD-DEMO%'")
cur.execute("DELETE FROM cards WHERE id LIKE 'CARD-DEMO%'")
print(f"   Đã xóa {cur.rowcount} records CARD-DEMO")

# ── 2. Insert lại đúng encoding ──
print("2. Insert lại CARD-DEMO đúng encoding...")
demo_cards = [
    ('CARD-DEMO-001', 'Nguyễn Văn A', '0901234567', 'nguyenvana@email.com', 150000),
    ('CARD-DEMO-002', 'Trần Thị B',   '0912345678', 'tranthib@email.com',   80000),
    ('CARD-DEMO-003', 'Lê Văn C',     '0923456789', None,                   200000),
]
for card in demo_cards:
    cur.execute(
        "INSERT INTO cards (id, name, phone, email, balance) VALUES (?, ?, ?, ?, ?)",
        card
    )
    print(f"   Inserted: {card[0]} | {card[1]}")

# ── 3. Chuẩn hóa vehicle_type ──
print("3. Chuẩn hóa vehicle_type...")
cur.execute("UPDATE vehicles SET vehicle_type = N'Xe máy' WHERE vehicle_type = 'motorbike'")
print(f"   motorbike -> Xe máy: {cur.rowcount} records")
cur.execute("UPDATE vehicles SET vehicle_type = N'Xe hơi' WHERE vehicle_type = 'car'")
print(f"   car -> Xe hơi: {cur.rowcount} records")

# ── 4. Chuẩn hóa plate_type ──
print("4. Chuẩn hóa plate_type...")
cur.execute("UPDATE vehicles SET plate_type = N'Biển thường' WHERE plate_type = 'Thường' OR plate_type = N'Thường'")
print(f"   Thường -> Biển thường: {cur.rowcount} records")

# ── 5. Chuẩn hóa plate_color ──
print("5. Kiểm tra plate_color...")
cur.execute("SELECT DISTINCT plate_color FROM vehicles")
colors = [r[0] for r in cur.fetchall()]
print(f"   Colors in DB: {colors}")

conn.commit()
conn.close()

print("\n✅ Hoàn tất! Kiểm tra lại:")
# Verify
conn2 = pyodbc.connect(
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=LAPTOP-3J6T1I18\\SQLEXPRESS01;'
    'DATABASE=ParkingManagement;'
    'Trusted_Connection=yes;'
)
conn2.setdecoding(pyodbc.SQL_CHAR,  encoding='cp1252')
conn2.setdecoding(pyodbc.SQL_WCHAR, encoding='utf-16-le')
conn2.setencoding(encoding='utf-16-le')
cur2 = conn2.cursor()
cur2.execute("SELECT id, name FROM cards ORDER BY created_at")
for r in cur2.fetchall():
    print(f"  {r[0]:20} | {r[1]}")
cur2.execute("SELECT DISTINCT vehicle_type FROM vehicles")
print("vehicle_types:", [r[0] for r in cur2.fetchall()])
conn2.close()

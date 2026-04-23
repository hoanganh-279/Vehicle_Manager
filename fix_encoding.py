"""
fix_encoding.py — Sửa dữ liệu tiếng Việt bị lỗi encoding trong DB
Chạy: python fix_encoding.py
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
conn.setencoding(encoding='utf-8')
cur = conn.cursor()

# ── 1. Xem tất cả cards ──
print("=== CARDS ===")
cur.execute("SELECT id, name, phone, email, balance FROM cards ORDER BY created_at")
cards = cur.fetchall()
for r in cards:
    print(f"  {r[0]!r:20} | {r[1]!r:30} | {r[2]} | bal={r[4]}")

# ── 2. Xem vehicles bị lỗi ──
print("\n=== VEHICLES (plate_color, vehicle_type) ===")
cur.execute("SELECT TOP 10 id, license_plate, plate_color, vehicle_type, plate_type FROM vehicles ORDER BY id")
for r in cur.fetchall():
    print(f"  id={r[0]} | {r[1]} | color={r[2]!r} | type={r[3]!r} | plate_type={r[4]!r}")

# ── 3. Xem topup_transactions ──
print("\n=== TOPUP_TRANSACTIONS ===")
cur.execute("SELECT TOP 5 id, card_id, amount, payment_method, status FROM topup_transactions ORDER BY id")
for r in cur.fetchall():
    print(f"  id={r[0]} | card={r[1]} | amt={r[2]} | method={r[3]!r} | status={r[4]!r}")

conn.close()
print("\nDone.")

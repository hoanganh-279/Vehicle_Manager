"""
fix_vehicles.py — Fix vehicle_type và plate_color trong DB
Dùng pyodbc với Unicode string trực tiếp
"""
import pyodbc

# Kết nối không set encoding để dùng default Unicode của pyodbc
conn = pyodbc.connect(
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=LAPTOP-3J6T1I18\\SQLEXPRESS01;'
    'DATABASE=ParkingManagement;'
    'Trusted_Connection=yes;'
    'unicode_results=yes;'
)

cur = conn.cursor()

# Xem dữ liệu hiện tại (raw bytes)
cur.execute("SELECT DISTINCT vehicle_type, CONVERT(VARBINARY(50), vehicle_type) FROM vehicles")
print("Current vehicle_types (with hex):")
for r in cur.fetchall():
    print(f"  {r[0]!r} -> {r[1].hex() if r[1] else None}")

cur.execute("SELECT DISTINCT plate_color, CONVERT(VARBINARY(50), plate_color) FROM vehicles")
print("\nCurrent plate_colors (with hex):")
for r in cur.fetchall():
    print(f"  {r[0]!r} -> {r[1].hex() if r[1] else None}")

conn.close()

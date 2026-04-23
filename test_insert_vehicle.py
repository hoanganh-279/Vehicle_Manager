"""
Script test INSERT vào bảng vehicles
Chạy: python test_insert_vehicle.py
"""

import pyodbc
from datetime import datetime

# Cấu hình database
DB_SERVER = r'LAPTOP-3J6T1I18\SQLEXPRESS01'
DB_DATABASE = 'ParkingManagement'
DB_DRIVER = 'ODBC Driver 17 for SQL Server'

def get_db():
    conn = pyodbc.connect(
        f'DRIVER={{{DB_DRIVER}}};'
        f'SERVER={DB_SERVER};'
        f'DATABASE={DB_DATABASE};'
        f'Trusted_Connection=yes;'
    )
    conn.setdecoding(pyodbc.SQL_WCHAR, encoding='utf-16-le')
    conn.setencoding(encoding='utf-16-le')
    return conn

def test_insert():
    print("=" * 70)
    print("TEST INSERT VÀO BẢNG VEHICLES")
    print("=" * 70)
    
    # Dữ liệu test
    license_plate = "TEST-123.45"
    plate_color = "Trắng"
    vehicle_type = "Xe máy"
    plate_type = "Biển thường"
    card_id = None
    
    print(f"\n📝 Dữ liệu test:")
    print(f"   - Biển số: {license_plate}")
    print(f"   - Màu biển: {plate_color}")
    print(f"   - Loại xe: {vehicle_type}")
    print(f"   - Loại biển: {plate_type}")
    print(f"   - Card ID: {card_id}")
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Test 1: INSERT cơ bản
        print(f"\n🧪 Test 1: INSERT với các cột cơ bản...")
        
        query = """INSERT INTO vehicles
                   (license_plate, plate_color, vehicle_type, plate_type, status, entry_time, card_id)
                   VALUES (?, ?, ?, ?, 'parked', ?, ?)"""
        
        params = [license_plate, plate_color, vehicle_type, plate_type, datetime.now(), card_id]
        
        print(f"   Query: {query}")
        print(f"   Params: {params}")
        
        cursor.execute(query, params)
        
        print(f"   ✅ Execute thành công!")
        print(f"   Rowcount: {cursor.rowcount}")
        
        # Lấy ID vừa tạo NGAY SAU INSERT, TRƯỚC KHI COMMIT
        print(f"   🔍 Đang lấy SCOPE_IDENTITY()...")
        cursor.execute("SELECT CAST(SCOPE_IDENTITY() AS INT) AS id")
        row = cursor.fetchone()
        
        print(f"   Row từ SCOPE_IDENTITY(): {row}")
        
        vehicle_id = int(row[0]) if row and row[0] else None
        
        print(f"   Vehicle ID parsed: {vehicle_id}")
        
        # Thử cách khác: Lấy MAX(id)
        print(f"   🔍 Thử lấy MAX(id)...")
        cursor.execute("SELECT MAX(id) FROM vehicles WHERE license_plate = ?", [license_plate])
        max_row = cursor.fetchone()
        print(f"   MAX(id): {max_row}")
        
        if not vehicle_id and max_row and max_row[0]:
            vehicle_id = int(max_row[0])
            print(f"   ✅ Dùng MAX(id): {vehicle_id}")
        
        conn.commit()
        
        print(f"   ✅ INSERT thành công!")
        print(f"   Vehicle ID: {vehicle_id}")
        
        # Test 2: Kiểm tra dữ liệu vừa INSERT
        print(f"\n🔍 Test 2: Kiểm tra dữ liệu vừa INSERT...")
        
        cursor.execute("SELECT * FROM vehicles WHERE id = ?", [vehicle_id])
        columns = [col[0] for col in cursor.description]
        row = cursor.fetchone()
        
        if row:
            print(f"   ✅ Tìm thấy xe vừa thêm:")
            for col, val in zip(columns, row):
                print(f"      {col}: {val}")
        else:
            print(f"   ❌ Không tìm thấy xe vừa thêm!")
        
        # Test 3: Xóa dữ liệu test
        print(f"\n🗑️  Test 3: Xóa dữ liệu test...")
        cursor.execute("DELETE FROM vehicles WHERE id = ?", [vehicle_id])
        conn.commit()
        print(f"   ✅ Đã xóa xe test (ID: {vehicle_id})")
        
        conn.close()
        
        print(f"\n" + "=" * 70)
        print("✅ TẤT CẢ TEST ĐỀU THÀNH CÔNG!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ LỖI:")
        print(f"   {str(e)}")
        
        import traceback
        print(f"\n📋 Traceback:")
        traceback.print_exc()
        
        print(f"\n" + "=" * 70)
        print("❌ TEST THẤT BẠI!")
        print("=" * 70)

if __name__ == "__main__":
    test_insert()

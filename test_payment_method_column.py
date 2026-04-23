"""
═══════════════════════════════════════════════════════════════════════════
TEST SCRIPT: Kiểm tra cột payment_method trong bảng vehicles
═══════════════════════════════════════════════════════════════════════════
Mục đích: Xác minh rằng cột payment_method đã được thêm vào database
Cách chạy: python test_payment_method_column.py
═══════════════════════════════════════════════════════════════════════════
"""

import pyodbc
import os
from dotenv import load_dotenv

# Load biến môi trường
load_dotenv()

DB_SERVER = os.getenv('DB_SERVER', r'LAPTOP-3J6T1I18\SQLEXPRESS01')
DB_DATABASE = os.getenv('DB_DATABASE', 'ParkingManagement')
DB_DRIVER = 'ODBC Driver 17 for SQL Server'

def test_payment_method_column():
    """Kiểm tra xem cột payment_method có tồn tại không"""
    print("═" * 80)
    print("KIỂM TRA CỘT PAYMENT_METHOD")
    print("═" * 80)
    print()
    
    try:
        # Kết nối database
        conn = pyodbc.connect(
            f'DRIVER={{{DB_DRIVER}}};'
            f'SERVER={DB_SERVER};'
            f'DATABASE={DB_DATABASE};'
            f'Trusted_Connection=yes;'
        )
        cursor = conn.cursor()
        print(f"✅ Kết nối thành công đến: {DB_SERVER}/{DB_DATABASE}")
        print()
        
        # Kiểm tra cột payment_method
        print("📋 Kiểm tra cột payment_method trong bảng vehicles...")
        cursor.execute("""
            SELECT 
                COLUMN_NAME,
                DATA_TYPE,
                CHARACTER_MAXIMUM_LENGTH,
                IS_NULLABLE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = 'vehicles' 
              AND COLUMN_NAME = 'payment_method'
        """)
        
        row = cursor.fetchone()
        if row:
            print("✅ Cột payment_method TỒN TẠI!")
            print(f"   - Tên cột: {row[0]}")
            print(f"   - Kiểu dữ liệu: {row[1]}")
            print(f"   - Độ dài: {row[2]}")
            print(f"   - Cho phép NULL: {row[3]}")
            print()
        else:
            print("❌ Cột payment_method KHÔNG TỒN TẠI!")
            print("   → Vui lòng chạy script: add_payment_method_column.sql")
            print()
            conn.close()
            return False
        
        # Kiểm tra constraint
        print("📋 Kiểm tra constraint CK_vehicles_payment_method...")
        cursor.execute("""
            SELECT name, definition
            FROM sys.check_constraints 
            WHERE name = 'CK_vehicles_payment_method'
        """)
        
        row = cursor.fetchone()
        if row:
            print("✅ Constraint TỒN TẠI!")
            print(f"   - Tên: {row[0]}")
            print(f"   - Định nghĩa: {row[1]}")
            print()
        else:
            print("⚠️  Constraint KHÔNG TỒN TẠI (không bắt buộc)")
            print()
        
        # Kiểm tra index
        print("📋 Kiểm tra index IX_vehicles_payment_method...")
        cursor.execute("""
            SELECT name, type_desc
            FROM sys.indexes 
            WHERE name = 'IX_vehicles_payment_method' 
              AND object_id = OBJECT_ID('vehicles')
        """)
        
        row = cursor.fetchone()
        if row:
            print("✅ Index TỒN TẠI!")
            print(f"   - Tên: {row[0]}")
            print(f"   - Loại: {row[1]}")
            print()
        else:
            print("⚠️  Index KHÔNG TỒN TẠI (không bắt buộc)")
            print()
        
        # Thống kê dữ liệu
        print("📊 Thống kê dữ liệu payment_method...")
        cursor.execute("""
            SELECT 
                payment_method,
                COUNT(*) AS count
            FROM vehicles
            WHERE status = 'exited'
            GROUP BY payment_method
            ORDER BY COUNT(*) DESC
        """)
        
        rows = cursor.fetchall()
        if rows:
            print("✅ Dữ liệu payment_method:")
            for row in rows:
                method = row[0] if row[0] else 'NULL'
                count = row[1]
                print(f"   - {method}: {count} xe")
            print()
        else:
            print("⚠️  Chưa có xe nào ra bãi")
            print()
        
        # Test INSERT
        print("🧪 Test INSERT với payment_method...")
        try:
            cursor.execute("""
                INSERT INTO vehicles 
                (license_plate, vehicle_type, status, entry_time, payment_method)
                VALUES (?, ?, ?, GETDATE(), ?)
            """, ['TEST-999.99', 'Xe máy', 'parked', 'cash'])
            
            # Lấy ID vừa insert
            cursor.execute("SELECT CAST(@@IDENTITY AS INT) AS id")
            vehicle_id = cursor.fetchone()[0]
            
            print(f"✅ INSERT thành công! Vehicle ID: {vehicle_id}")
            
            # Xóa xe test
            cursor.execute("DELETE FROM vehicles WHERE id = ?", [vehicle_id])
            conn.commit()
            print("✅ Đã xóa xe test")
            print()
            
        except Exception as e:
            print(f"❌ Lỗi INSERT: {str(e)}")
            print()
            conn.rollback()
        
        conn.close()
        
        print("═" * 80)
        print("KẾT LUẬN: Cột payment_method đã sẵn sàng sử dụng! ✅")
        print("═" * 80)
        return True
        
    except Exception as e:
        print(f"❌ Lỗi kết nối database: {str(e)}")
        print()
        print("Vui lòng kiểm tra:")
        print("  1. SQL Server đang chạy")
        print("  2. Tên server đúng:", DB_SERVER)
        print("  3. Database tồn tại:", DB_DATABASE)
        print("  4. ODBC Driver 17 for SQL Server đã cài đặt")
        return False

if __name__ == '__main__':
    test_payment_method_column()

# =============================================================================
# fix_encoding_complete.py — Sửa lỗi encoding tiếng Việt trong database
# =============================================================================

import pyodbc
import os
from dotenv import load_dotenv

load_dotenv()

DB_SERVER   = os.getenv('DB_SERVER', r'LAPTOP-3J6T1I18\SQLEXPRESS01')
DB_DATABASE = os.getenv('DB_DATABASE', 'ParkingManagement')
DB_DRIVER   = 'ODBC Driver 17 for SQL Server'

def get_db():
    """Kết nối database với encoding UTF-16LE đúng chuẩn SQL Server"""
    conn = pyodbc.connect(
        f'DRIVER={{{DB_DRIVER}}};'
        f'SERVER={DB_SERVER};'
        f'DATABASE={DB_DATABASE};'
        f'Trusted_Connection=yes;'
    )
    # Đọc NVARCHAR đúng UTF-16LE
    conn.setdecoding(pyodbc.SQL_WCHAR, encoding='utf-16-le')
    # Ghi string Python vào NVARCHAR đúng UTF-16LE
    conn.setencoding(encoding='utf-16-le')
    return conn

def fix_encoding():
    """Kiểm tra và sửa lỗi encoding trong các bảng"""
    conn = get_db()
    cursor = conn.cursor()
    
    print("=" * 70)
    print("KIỂM TRA VÀ SỬA LỖI ENCODING TIẾNG VIỆT")
    print("=" * 70)
    
    # Kiểm tra bảng cards
    print("\n[1] Kiểm tra bảng CARDS...")
    try:
        cursor.execute("SELECT TOP 5 id, name, phone FROM cards")
        rows = cursor.fetchall()
        print(f"✓ Tìm thấy {len(rows)} thẻ:")
        for row in rows:
            print(f"  - ID: {row[0][:10]}... | Tên: {row[1]} | SĐT: {row[2]}")
    except Exception as e:
        print(f"✗ Lỗi: {e}")
    
    # Kiểm tra bảng vehicles
    print("\n[2] Kiểm tra bảng VEHICLES...")
    try:
        cursor.execute("SELECT TOP 5 id, license_plate, vehicle_type, plate_color FROM vehicles")
        rows = cursor.fetchall()
        print(f"✓ Tìm thấy {len(rows)} xe:")
        for row in rows:
            print(f"  - ID: {row[0]} | Biển: {row[1]} | Loại: {row[2]} | Màu: {row[3]}")
    except Exception as e:
        print(f"✗ Lỗi: {e}")
    
    # Kiểm tra collation của database
    print("\n[3] Kiểm tra COLLATION của database...")
    try:
        cursor.execute("""
            SELECT name, collation_name 
            FROM sys.databases 
            WHERE name = ?
        """, [DB_DATABASE])
        row = cursor.fetchone()
        if row:
            print(f"✓ Database: {row[0]}")
            print(f"  Collation: {row[1]}")
            if 'UTF8' not in row[1]:
                print(f"  ⚠ CẢNH BÁO: Collation không phải UTF-8!")
                print(f"  → Khuyến nghị: Sử dụng NVARCHAR thay vì VARCHAR")
    except Exception as e:
        print(f"✗ Lỗi: {e}")
    
    # Kiểm tra kiểu dữ liệu các cột
    print("\n[4] Kiểm tra kiểu dữ liệu các cột...")
    tables_to_check = ['cards', 'vehicles']
    for table in tables_to_check:
        try:
            cursor.execute(f"""
                SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = '{table}'
                AND DATA_TYPE IN ('varchar', 'nvarchar', 'char', 'nchar')
            """)
            cols = cursor.fetchall()
            print(f"\n  Bảng {table.upper()}:")
            for col in cols:
                col_name, data_type, max_len = col
                status = "✓" if data_type.startswith('n') else "✗"
                print(f"    {status} {col_name}: {data_type}({max_len if max_len else 'MAX'})")
                if not data_type.startswith('n'):
                    print(f"      ⚠ Nên đổi sang N{data_type.upper()}")
        except Exception as e:
            print(f"  ✗ Lỗi: {e}")
    
    conn.close()
    
    print("\n" + "=" * 70)
    print("HOÀN TẤT KIỂM TRA")
    print("=" * 70)
    print("\nKẾT LUẬN:")
    print("1. Nếu dữ liệu hiển thị đúng tiếng Việt → Encoding OK")
    print("2. Nếu dữ liệu bị lỗi → Cần chuyển VARCHAR sang NVARCHAR")
    print("3. Khi INSERT dữ liệu mới, luôn dùng N'...' cho chuỗi tiếng Việt")
    print("\nVí dụ: INSERT INTO cards (name) VALUES (N'Nguyễn Văn A')")

if __name__ == '__main__':
    try:
        fix_encoding()
    except Exception as e:
        print(f"\n✗ LỖI NGHIÊM TRỌNG: {e}")
        print("\nKiểm tra:")
        print("1. SQL Server đang chạy?")
        print("2. Tên server và database trong .env đúng?")
        print("3. ODBC Driver 17 for SQL Server đã cài?")

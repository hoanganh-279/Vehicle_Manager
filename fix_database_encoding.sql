-- =============================================================================
-- fix_database_encoding.sql
-- Script sửa lỗi encoding tiếng Việt trong SQL Server
-- =============================================================================

USE ParkingManagement;
GO

PRINT '========================================';
PRINT 'KIỂM TRA VÀ SỬA LỖI ENCODING';
PRINT '========================================';
PRINT '';

-- ============================================================================
-- BƯỚC 1: Kiểm tra Collation hiện tại
-- ============================================================================
PRINT '[1] Kiểm tra Collation của Database...';
SELECT 
    name AS DatabaseName,
    collation_name AS Collation
FROM sys.databases 
WHERE name = 'ParkingManagement';
PRINT '';

-- ============================================================================
-- BƯỚC 2: Kiểm tra kiểu dữ liệu các cột
-- ============================================================================
PRINT '[2] Kiểm tra kiểu dữ liệu các cột chứa tiếng Việt...';
PRINT '';

PRINT '--- Bảng CARDS ---';
SELECT 
    COLUMN_NAME AS ColumnName,
    DATA_TYPE AS DataType,
    CHARACTER_MAXIMUM_LENGTH AS MaxLength,
    CASE 
        WHEN DATA_TYPE LIKE 'n%' THEN 'OK (Unicode)'
        ELSE 'CẢNH BÁO (Không Unicode)'
    END AS Status
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'cards'
AND DATA_TYPE IN ('varchar', 'nvarchar', 'char', 'nchar')
ORDER BY ORDINAL_POSITION;
PRINT '';

PRINT '--- Bảng VEHICLES ---';
SELECT 
    COLUMN_NAME AS ColumnName,
    DATA_TYPE AS DataType,
    CHARACTER_MAXIMUM_LENGTH AS MaxLength,
    CASE 
        WHEN DATA_TYPE LIKE 'n%' THEN 'OK (Unicode)'
        ELSE 'CẢNH BÁO (Không Unicode)'
    END AS Status
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'vehicles'
AND DATA_TYPE IN ('varchar', 'nvarchar', 'char', 'nchar')
ORDER BY ORDINAL_POSITION;
PRINT '';

-- ============================================================================
-- BƯỚC 3: Kiểm tra dữ liệu mẫu
-- ============================================================================
PRINT '[3] Kiểm tra dữ liệu mẫu...';
PRINT '';

PRINT '--- Top 5 thẻ ---';
SELECT TOP 5 
    id,
    name,
    phone,
    email
FROM cards
ORDER BY created_at DESC;
PRINT '';

PRINT '--- Top 5 xe ---';
SELECT TOP 5 
    id,
    license_plate,
    vehicle_type,
    plate_color
FROM vehicles
ORDER BY entry_time DESC;
PRINT '';

-- ============================================================================
-- BƯỚC 4: SỬA LỖI (Chỉ chạy nếu cần thiết)
-- ============================================================================
PRINT '========================================';
PRINT 'HƯỚNG DẪN SỬA LỖI';
PRINT '========================================';
PRINT '';
PRINT 'Nếu các cột đang dùng VARCHAR (không phải NVARCHAR),';
PRINT 'hãy UNCOMMENT (bỏ dấu --) các lệnh ALTER TABLE bên dưới:';
PRINT '';

-- CẢNH BÁO: Chỉ chạy các lệnh này nếu cột đang là VARCHAR!
-- Bỏ dấu -- ở đầu dòng để kích hoạt

-- Sửa bảng CARDS
-- ALTER TABLE cards ALTER COLUMN id NVARCHAR(50);
-- ALTER TABLE cards ALTER COLUMN name NVARCHAR(255);
-- ALTER TABLE cards ALTER COLUMN phone NVARCHAR(20);
-- ALTER TABLE cards ALTER COLUMN email NVARCHAR(255);

-- Sửa bảng VEHICLES
-- ALTER TABLE vehicles ALTER COLUMN license_plate NVARCHAR(20);
-- ALTER TABLE vehicles ALTER COLUMN plate_color NVARCHAR(50);
-- ALTER TABLE vehicles ALTER COLUMN vehicle_type NVARCHAR(50);
-- ALTER TABLE vehicles ALTER COLUMN plate_type NVARCHAR(50);

PRINT '';
PRINT '========================================';
PRINT 'LƯU Ý QUAN TRỌNG';
PRINT '========================================';
PRINT '';
PRINT '1. Khi INSERT dữ liệu mới, LUÔN dùng N prefix:';
PRINT '   INSERT INTO cards (name) VALUES (N''Nguyễn Văn A'')';
PRINT '';
PRINT '2. Trong Python, đảm bảo connection đã set encoding:';
PRINT '   conn.setencoding(encoding=''utf-16-le'')';
PRINT '';
PRINT '3. Nếu dữ liệu cũ đã bị lỗi, cần UPDATE lại:';
PRINT '   UPDATE cards SET name = N''Tên đúng'' WHERE id = ''...'';';
PRINT '';

-- ============================================================================
-- BƯỚC 5: Test INSERT dữ liệu tiếng Việt
-- ============================================================================
PRINT '[4] Test INSERT dữ liệu tiếng Việt...';
PRINT '';

-- Test INSERT (sẽ rollback, không lưu vào DB)
BEGIN TRANSACTION;

DECLARE @test_id NVARCHAR(50) = 'TEST-' + CONVERT(NVARCHAR(50), NEWID());

INSERT INTO cards (id, name, phone, email, balance, created_at)
VALUES (
    @test_id,
    N'Nguyễn Văn A',
    N'0901234567',
    N'test@example.com',
    100000,
    GETDATE()
);

-- Kiểm tra dữ liệu vừa INSERT
SELECT 
    id,
    name,
    phone,
    CASE 
        WHEN name = N'Nguyễn Văn A' THEN 'OK - Tiếng Việt đúng'
        ELSE 'LỖI - Tiếng Việt bị sai'
    END AS EncodingStatus
FROM cards
WHERE id = @test_id;

-- Rollback để không lưu dữ liệu test
ROLLBACK TRANSACTION;

PRINT '';
PRINT 'Test INSERT hoàn tất (đã rollback, không lưu vào DB)';
PRINT '';

-- ============================================================================
-- KẾT LUẬN
-- ============================================================================
PRINT '========================================';
PRINT 'KẾT LUẬN';
PRINT '========================================';
PRINT '';
PRINT 'Nếu test INSERT hiển thị "OK - Tiếng Việt đúng":';
PRINT '  → Encoding đã đúng, không cần sửa gì';
PRINT '';
PRINT 'Nếu test INSERT hiển thị "LỖI - Tiếng Việt bị sai":';
PRINT '  → Cần chuyển các cột từ VARCHAR sang NVARCHAR';
PRINT '  → Uncomment các lệnh ALTER TABLE ở BƯỚC 4';
PRINT '';
PRINT 'Sau khi sửa xong, chạy lại script này để kiểm tra';
PRINT '';

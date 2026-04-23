-- ═══════════════════════════════════════════════════════════════════════════
-- SQL SCRIPT: Thêm cột payment_method vào bảng vehicles
-- Mục đích: Lưu phương thức thanh toán khi xe ra bãi
-- ═══════════════════════════════════════════════════════════════════════════

USE ParkingManagement;
GO

PRINT '═══════════════════════════════════════════════════════════════════════════';
PRINT 'BẮT ĐẦU THÊM CỘT PAYMENT_METHOD';
PRINT '═══════════════════════════════════════════════════════════════════════════';
PRINT '';

-- Kiểm tra và thêm cột payment_method vào bảng vehicles
IF NOT EXISTS (
    SELECT * FROM sys.columns 
    WHERE object_id = OBJECT_ID('vehicles') 
    AND name = 'payment_method'
)
BEGIN
    ALTER TABLE vehicles
    ADD payment_method NVARCHAR(50) NULL;
    
    PRINT '✅ Đã thêm cột payment_method vào bảng vehicles';
    PRINT '   - Kiểu dữ liệu: NVARCHAR(50)';
    PRINT '   - Cho phép NULL: YES';
    PRINT '   - Giá trị mặc định: NULL';
END
ELSE
BEGIN
    PRINT '⚠️  Cột payment_method đã tồn tại trong bảng vehicles';
END
GO

-- Thêm constraint để validate giá trị payment_method
IF NOT EXISTS (
    SELECT * FROM sys.check_constraints 
    WHERE name = 'CK_vehicles_payment_method'
)
BEGIN
    ALTER TABLE vehicles
    ADD CONSTRAINT CK_vehicles_payment_method
    CHECK (payment_method IN ('cash', 'member_card', 'momo', 'vnpay', 'stripe', NULL));
    
    PRINT '✅ Đã thêm constraint CK_vehicles_payment_method';
    PRINT '   - Giá trị hợp lệ: cash, member_card, momo, vnpay, stripe, NULL';
END
ELSE
BEGIN
    PRINT '⚠️  Constraint CK_vehicles_payment_method đã tồn tại';
END
GO

-- Tạo index để tăng tốc truy vấn theo payment_method
IF NOT EXISTS (
    SELECT * FROM sys.indexes 
    WHERE name = 'IX_vehicles_payment_method' 
    AND object_id = OBJECT_ID('vehicles')
)
BEGIN
    CREATE INDEX IX_vehicles_payment_method 
    ON vehicles(payment_method)
    WHERE payment_method IS NOT NULL;
    
    PRINT '✅ Đã tạo index IX_vehicles_payment_method';
END
ELSE
BEGIN
    PRINT '⚠️  Index IX_vehicles_payment_method đã tồn tại';
END
GO

-- Cập nhật giá trị mặc định cho các xe đã thanh toán trước đó
UPDATE vehicles
SET payment_method = 'cash'
WHERE status = 'exited' 
  AND payment_status = 'paid'
  AND payment_method IS NULL;

DECLARE @updated_count INT = @@ROWCOUNT;
PRINT '';
PRINT '✅ Đã cập nhật ' + CAST(@updated_count AS NVARCHAR(10)) + ' xe đã thanh toán trước đó với payment_method = ''cash''';
GO

-- Hiển thị thông tin cột vừa tạo
PRINT '';
PRINT '═══════════════════════════════════════════════════════════════════════════';
PRINT 'THÔNG TIN CỘT PAYMENT_METHOD';
PRINT '═══════════════════════════════════════════════════════════════════════════';

SELECT 
    COLUMN_NAME AS 'Tên cột',
    DATA_TYPE AS 'Kiểu dữ liệu',
    CHARACTER_MAXIMUM_LENGTH AS 'Độ dài',
    IS_NULLABLE AS 'Cho phép NULL'
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'vehicles' 
  AND COLUMN_NAME = 'payment_method';
GO

PRINT '';
PRINT '═══════════════════════════════════════════════════════════════════════════';
PRINT 'HOÀN TẤT THÊM CỘT PAYMENT_METHOD';
PRINT '═══════════════════════════════════════════════════════════════════════════';
PRINT '';
PRINT 'Các phương thức thanh toán hợp lệ:';
PRINT '  - cash: Tiền mặt';
PRINT '  - member_card: Thẻ thành viên';
PRINT '  - momo: MoMo';
PRINT '  - vnpay: VNPay';
PRINT '  - stripe: Stripe';
PRINT '';
PRINT 'Sử dụng:';
PRINT '  UPDATE vehicles SET payment_method = ''cash'' WHERE id = 1;';
PRINT '═══════════════════════════════════════════════════════════════════════════';
GO

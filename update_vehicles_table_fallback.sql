-- ═══════════════════════════════════════════════════════════════════════════
-- SQL SCRIPT: Cập nhật bảng vehicles để hỗ trợ Fallback Workflow
-- Mục đích: Thêm các trường audit trail cho trường hợp OCR thất bại
-- ═══════════════════════════════════════════════════════════════════════════

USE ParkingManagement;
GO

-- Kiểm tra và thêm cột is_manual_entry (đánh dấu nhập tay)
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('vehicles') AND name = 'is_manual_entry')
BEGIN
    ALTER TABLE vehicles
    ADD is_manual_entry BIT DEFAULT 0;
    PRINT 'Đã thêm cột is_manual_entry';
END
ELSE
BEGIN
    PRINT 'Cột is_manual_entry đã tồn tại';
END
GO

-- Kiểm tra và thêm cột is_suspicious (đánh dấu xe nghi ngờ)
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('vehicles') AND name = 'is_suspicious')
BEGIN
    ALTER TABLE vehicles
    ADD is_suspicious BIT DEFAULT 0;
    PRINT 'Đã thêm cột is_suspicious';
END
ELSE
BEGIN
    PRINT 'Cột is_suspicious đã tồn tại';
END
GO

-- Kiểm tra và thêm cột entry_method (phương thức nhập: 'ocr' hoặc 'manual')
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('vehicles') AND name = 'entry_method')
BEGIN
    ALTER TABLE vehicles
    ADD entry_method NVARCHAR(20) DEFAULT 'ocr';
    PRINT 'Đã thêm cột entry_method';
END
ELSE
BEGIN
    PRINT 'Cột entry_method đã tồn tại';
END
GO

-- Kiểm tra và thêm cột snapshot_image_path (đường dẫn ảnh chụp)
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('vehicles') AND name = 'snapshot_image_path')
BEGIN
    ALTER TABLE vehicles
    ADD snapshot_image_path NVARCHAR(500) NULL;
    PRINT 'Đã thêm cột snapshot_image_path';
END
ELSE
BEGIN
    PRINT 'Cột snapshot_image_path đã tồn tại';
END
GO

-- Kiểm tra và thêm cột capture_timestamp (thời điểm chụp ảnh)
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('vehicles') AND name = 'capture_timestamp')
BEGIN
    ALTER TABLE vehicles
    ADD capture_timestamp DATETIME NULL;
    PRINT 'Đã thêm cột capture_timestamp';
END
ELSE
BEGIN
    PRINT 'Cột capture_timestamp đã tồn tại';
END
GO

-- Kiểm tra và thêm cột audit_metadata (JSON metadata cho audit trail)
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('vehicles') AND name = 'audit_metadata')
BEGIN
    ALTER TABLE vehicles
    ADD audit_metadata NVARCHAR(MAX) NULL;
    PRINT 'Đã thêm cột audit_metadata';
END
ELSE
BEGIN
    PRINT 'Cột audit_metadata đã tồn tại';
END
GO

-- Kiểm tra và thêm cột manual_override_reason (lý do nhập tay)
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('vehicles') AND name = 'manual_override_reason')
BEGIN
    ALTER TABLE vehicles
    ADD manual_override_reason NVARCHAR(500) NULL;
    PRINT 'Đã thêm cột manual_override_reason';
END
ELSE
BEGIN
    PRINT 'Cột manual_override_reason đã tồn tại';
END
GO

-- Tạo index để tăng tốc truy vấn các xe nghi ngờ
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_vehicles_suspicious' AND object_id = OBJECT_ID('vehicles'))
BEGIN
    CREATE INDEX IX_vehicles_suspicious ON vehicles(is_suspicious, status)
    WHERE is_suspicious = 1;
    PRINT 'Đã tạo index IX_vehicles_suspicious';
END
ELSE
BEGIN
    PRINT 'Index IX_vehicles_suspicious đã tồn tại';
END
GO

-- Tạo index để tăng tốc truy vấn các xe nhập tay
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_vehicles_manual_entry' AND object_id = OBJECT_ID('vehicles'))
BEGIN
    CREATE INDEX IX_vehicles_manual_entry ON vehicles(is_manual_entry, entry_time)
    WHERE is_manual_entry = 1;
    PRINT 'Đã tạo index IX_vehicles_manual_entry';
END
ELSE
BEGIN
    PRINT 'Index IX_vehicles_manual_entry đã tồn tại';
END
GO

-- ═══════════════════════════════════════════════════════════════════════════
-- Tạo View để dễ dàng tra soát các xe nghi ngờ
-- ═══════════════════════════════════════════════════════════════════════════
IF OBJECT_ID('vw_suspicious_vehicles', 'V') IS NOT NULL
    DROP VIEW vw_suspicious_vehicles;
GO

CREATE VIEW vw_suspicious_vehicles AS
SELECT 
    v.id,
    v.license_plate,
    v.vehicle_type,
    v.entry_time,
    v.exit_time,
    v.status,
    v.is_manual_entry,
    v.is_suspicious,
    v.entry_method,
    v.snapshot_image_path,
    v.capture_timestamp,
    v.manual_override_reason,
    v.audit_metadata,
    c.name AS card_holder_name,
    c.phone AS card_holder_phone,
    CASE 
        WHEN v.is_suspicious = 1 AND v.is_manual_entry = 1 THEN 'Nghi ngờ cao - Nhập tay'
        WHEN v.is_suspicious = 1 THEN 'Nghi ngờ - OCR'
        WHEN v.is_manual_entry = 1 THEN 'Nhập tay - Bình thường'
        ELSE 'Bình thường'
    END AS risk_level
FROM vehicles v
LEFT JOIN cards c ON v.card_id = c.id
WHERE v.is_suspicious = 1 OR v.is_manual_entry = 1;
GO

PRINT 'Đã tạo view vw_suspicious_vehicles';
GO

-- ═══════════════════════════════════════════════════════════════════════════
-- Tạo Stored Procedure để lấy báo cáo audit trail
-- ═══════════════════════════════════════════════════════════════════════════
IF OBJECT_ID('sp_get_audit_trail_report', 'P') IS NOT NULL
    DROP PROCEDURE sp_get_audit_trail_report;
GO

CREATE PROCEDURE sp_get_audit_trail_report
    @start_date DATE = NULL,
    @end_date DATE = NULL,
    @suspicious_only BIT = 0
AS
BEGIN
    SET NOCOUNT ON;
    
    IF @start_date IS NULL
        SET @start_date = CAST(GETDATE() AS DATE);
    
    IF @end_date IS NULL
        SET @end_date = CAST(GETDATE() AS DATE);
    
    SELECT 
        v.id AS vehicle_id,
        v.license_plate,
        v.vehicle_type,
        v.entry_time,
        v.exit_time,
        v.status,
        v.is_manual_entry,
        v.is_suspicious,
        v.entry_method,
        v.snapshot_image_path,
        v.capture_timestamp,
        v.manual_override_reason,
        v.audit_metadata,
        CASE 
            WHEN v.is_suspicious = 1 AND v.is_manual_entry = 1 THEN 'Nghi ngờ cao'
            WHEN v.is_suspicious = 1 THEN 'Nghi ngờ'
            WHEN v.is_manual_entry = 1 THEN 'Nhập tay'
            ELSE 'Bình thường'
        END AS risk_level,
        c.name AS card_holder_name,
        c.phone AS card_holder_phone
    FROM vehicles v
    LEFT JOIN cards c ON v.card_id = c.id
    WHERE 
        CAST(v.entry_time AS DATE) BETWEEN @start_date AND @end_date
        AND (@suspicious_only = 0 OR v.is_suspicious = 1)
    ORDER BY v.entry_time DESC;
END
GO

PRINT 'Đã tạo stored procedure sp_get_audit_trail_report';
GO

-- ═══════════════════════════════════════════════════════════════════════════
-- Thêm dữ liệu mẫu để test (optional)
-- ═══════════════════════════════════════════════════════════════════════════
PRINT '═══════════════════════════════════════════════════════════════════════════';
PRINT 'HOÀN TẤT CẬP NHẬT DATABASE SCHEMA CHO FALLBACK WORKFLOW';
PRINT '═══════════════════════════════════════════════════════════════════════════';
PRINT '';
PRINT 'Các cột đã thêm:';
PRINT '  - is_manual_entry: Đánh dấu xe nhập tay';
PRINT '  - is_suspicious: Đánh dấu xe nghi ngờ';
PRINT '  - entry_method: Phương thức nhập (ocr/manual)';
PRINT '  - snapshot_image_path: Đường dẫn ảnh chụp';
PRINT '  - capture_timestamp: Thời điểm chụp ảnh';
PRINT '  - audit_metadata: Metadata JSON cho audit trail';
PRINT '  - manual_override_reason: Lý do nhập tay';
PRINT '';
PRINT 'View đã tạo:';
PRINT '  - vw_suspicious_vehicles: Xem danh sách xe nghi ngờ';
PRINT '';
PRINT 'Stored Procedure đã tạo:';
PRINT '  - sp_get_audit_trail_report: Lấy báo cáo audit trail';
PRINT '';
PRINT 'Sử dụng:';
PRINT '  EXEC sp_get_audit_trail_report @start_date=''2025-01-01'', @end_date=''2025-12-31'', @suspicious_only=1';
PRINT '═══════════════════════════════════════════════════════════════════════════';
GO

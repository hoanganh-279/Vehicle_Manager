-- ═══════════════════════════════════════════════════════════════════════════
-- ROLLBACK PAYMENT SYSTEM - DATABASE SCHEMA
-- ═══════════════════════════════════════════════════════════════════════════
-- Script này rollback tất cả thay đổi từ fix_payment_critical.sql
-- Thời gian thực thi: 1-2 phút
-- ═══════════════════════════════════════════════════════════════════════════

USE ParkingManagement;
GO

PRINT '═══════════════════════════════════════════════════════════════════════════';
PRINT 'ROLLBACK PAYMENT SYSTEM - BẮT ĐẦU';
PRINT '═══════════════════════════════════════════════════════════════════════════';
PRINT '';

-- ═══════════════════════════════════════════════════════════════════════════
-- ROLLBACK #1: Xóa trigger
-- ═══════════════════════════════════════════════════════════════════════════
PRINT 'ROLLBACK #1: Xóa trigger trg_cards_balance_history';

IF EXISTS (SELECT * FROM sys.triggers WHERE name = 'trg_cards_balance_history')
BEGIN
    DROP TRIGGER trg_cards_balance_history;
    PRINT '✅ Đã xóa trigger trg_cards_balance_history';
END
ELSE
BEGIN
    PRINT '⚠️  Trigger trg_cards_balance_history không tồn tại';
END
GO

PRINT '';

-- ═══════════════════════════════════════════════════════════════════════════
-- ROLLBACK #2: Xóa view
-- ═══════════════════════════════════════════════════════════════════════════
PRINT 'ROLLBACK #2: Xóa view vw_pending_payments';

IF EXISTS (SELECT * FROM sys.views WHERE name = 'vw_pending_payments')
BEGIN
    DROP VIEW vw_pending_payments;
    PRINT '✅ Đã xóa view vw_pending_payments';
END
ELSE
BEGIN
    PRINT '⚠️  View vw_pending_payments không tồn tại';
END
GO

PRINT '';

-- ═══════════════════════════════════════════════════════════════════════════
-- ROLLBACK #3: Xóa stored procedure
-- ═══════════════════════════════════════════════════════════════════════════
PRINT 'ROLLBACK #3: Xóa stored procedure sp_check_balance_integrity';

IF EXISTS (SELECT * FROM sys.procedures WHERE name = 'sp_check_balance_integrity')
BEGIN
    DROP PROCEDURE sp_check_balance_integrity;
    PRINT '✅ Đã xóa stored procedure sp_check_balance_integrity';
END
ELSE
BEGIN
    PRINT '⚠️  Stored procedure sp_check_balance_integrity không tồn tại';
END
GO

PRINT '';

-- ═══════════════════════════════════════════════════════════════════════════
-- ROLLBACK #4: Xóa bảng balance_history
-- ═══════════════════════════════════════════════════════════════════════════
PRINT 'ROLLBACK #4: Xóa bảng balance_history';

IF EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'balance_history')
BEGIN
    -- Xóa indexes trước
    IF EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_card_created' AND object_id = OBJECT_ID('balance_history'))
    BEGIN
        DROP INDEX idx_card_created ON balance_history;
        PRINT '  ✅ Đã xóa index idx_card_created';
    END
    
    IF EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_transaction_id' AND object_id = OBJECT_ID('balance_history'))
    BEGIN
        DROP INDEX idx_transaction_id ON balance_history;
        PRINT '  ✅ Đã xóa index idx_transaction_id';
    END
    
    IF EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_type' AND object_id = OBJECT_ID('balance_history'))
    BEGIN
        DROP INDEX idx_type ON balance_history;
        PRINT '  ✅ Đã xóa index idx_type';
    END
    
    -- Xóa bảng
    DROP TABLE balance_history;
    PRINT '✅ Đã xóa bảng balance_history';
END
ELSE
BEGIN
    PRINT '⚠️  Bảng balance_history không tồn tại';
END
GO

PRINT '';

-- ═══════════════════════════════════════════════════════════════════════════
-- ROLLBACK #5: Xóa cột momo_trans_id và completed_at
-- ═══════════════════════════════════════════════════════════════════════════
PRINT 'ROLLBACK #5: Xóa cột momo_trans_id và completed_at từ topup_transactions';

IF EXISTS (
    SELECT * FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'topup_transactions' 
    AND COLUMN_NAME = 'momo_trans_id'
)
BEGIN
    -- Xóa index trước
    IF EXISTS (
        SELECT * FROM sys.indexes 
        WHERE name = 'idx_momo_trans_id'
        AND object_id = OBJECT_ID('topup_transactions')
    )
    BEGIN
        DROP INDEX idx_momo_trans_id ON topup_transactions;
        PRINT '  ✅ Đã xóa index idx_momo_trans_id';
    END
    
    -- Xóa cột
    ALTER TABLE topup_transactions
    DROP COLUMN momo_trans_id, completed_at;
    
    PRINT '✅ Đã xóa cột momo_trans_id và completed_at';
END
ELSE
BEGIN
    PRINT '⚠️  Cột momo_trans_id không tồn tại';
END
GO

PRINT '';

-- ═══════════════════════════════════════════════════════════════════════════
-- ROLLBACK #6: Xóa index idx_topup_status_created
-- ═══════════════════════════════════════════════════════════════════════════
PRINT 'ROLLBACK #6: Xóa index idx_topup_status_created';

IF EXISTS (
    SELECT * FROM sys.indexes 
    WHERE name = 'idx_topup_status_created'
    AND object_id = OBJECT_ID('topup_transactions')
)
BEGIN
    DROP INDEX idx_topup_status_created ON topup_transactions;
    PRINT '✅ Đã xóa index idx_topup_status_created';
END
ELSE
BEGIN
    PRINT '⚠️  Index idx_topup_status_created không tồn tại';
END
GO

PRINT '';

-- ═══════════════════════════════════════════════════════════════════════════
-- ROLLBACK #7: Xóa index idx_vehicles_status_entry
-- ═══════════════════════════════════════════════════════════════════════════
PRINT 'ROLLBACK #7: Xóa index idx_vehicles_status_entry';

IF EXISTS (
    SELECT * FROM sys.indexes 
    WHERE name = 'idx_vehicles_status_entry'
    AND object_id = OBJECT_ID('vehicles')
)
BEGIN
    DROP INDEX idx_vehicles_status_entry ON vehicles;
    PRINT '✅ Đã xóa index idx_vehicles_status_entry';
END
ELSE
BEGIN
    PRINT '⚠️  Index idx_vehicles_status_entry không tồn tại';
END
GO

PRINT '';

-- ═══════════════════════════════════════════════════════════════════════════
-- ROLLBACK #8: Xóa cột momo_trans_id từ vehicles (nếu có)
-- ═══════════════════════════════════════════════════════════════════════════
PRINT 'ROLLBACK #8: Xóa cột momo_trans_id từ vehicles';

IF EXISTS (
    SELECT * FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'vehicles' 
    AND COLUMN_NAME = 'momo_trans_id'
)
BEGIN
    -- Xóa index trước (nếu có)
    IF EXISTS (
        SELECT * FROM sys.indexes 
        WHERE name = 'idx_vehicles_momo_trans_id'
        AND object_id = OBJECT_ID('vehicles')
    )
    BEGIN
        DROP INDEX idx_vehicles_momo_trans_id ON vehicles;
        PRINT '  ✅ Đã xóa index idx_vehicles_momo_trans_id';
    END
    
    -- Xóa cột
    ALTER TABLE vehicles
    DROP COLUMN momo_trans_id;
    
    PRINT '✅ Đã xóa cột momo_trans_id từ vehicles';
END
ELSE
BEGIN
    PRINT '⚠️  Cột momo_trans_id không tồn tại trong vehicles';
END
GO

PRINT '';
PRINT '═══════════════════════════════════════════════════════════════════════════';
PRINT 'ROLLBACK HOÀN TẤT!';
PRINT '═══════════════════════════════════════════════════════════════════════════';
PRINT '';
PRINT 'Các thay đổi đã được rollback:';
PRINT '  ✅ Đã xóa trigger trg_cards_balance_history';
PRINT '  ✅ Đã xóa view vw_pending_payments';
PRINT '  ✅ Đã xóa stored procedure sp_check_balance_integrity';
PRINT '  ✅ Đã xóa bảng balance_history';
PRINT '  ✅ Đã xóa cột momo_trans_id và completed_at từ topup_transactions';
PRINT '  ✅ Đã xóa cột momo_trans_id từ vehicles';
PRINT '  ✅ Đã xóa các index';
PRINT '';
PRINT 'Bước tiếp theo:';
PRINT '  1. Verify database: SELECT * FROM topup_transactions';
PRINT '  2. Rollback code: git reset --hard <commit_hash>';
PRINT '  3. Start Flask app: python app.py';
PRINT '  4. Chạy script đối soát: python reconcile_transactions.py';
PRINT '';
PRINT '═══════════════════════════════════════════════════════════════════════════';

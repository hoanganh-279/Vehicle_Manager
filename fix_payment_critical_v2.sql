SET QUOTED_IDENTIFIER ON;
SET ANSI_NULLS ON;
GO

USE ParkingManagement;
GO

PRINT '═══════════════════════════════════════════════════════════════════════════';
PRINT 'FIX #1: Thêm cột momo_trans_id vào topup_transactions';
PRINT '═══════════════════════════════════════════════════════════════════════════';

IF NOT EXISTS (
    SELECT * FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'topup_transactions' 
    AND COLUMN_NAME = 'momo_trans_id'
)
BEGIN
    ALTER TABLE topup_transactions
    ADD momo_trans_id NVARCHAR(100) NULL;
    
    PRINT '✅ Đã thêm cột momo_trans_id';
END
ELSE
BEGIN
    PRINT '⚠️  Cột momo_trans_id đã tồn tại';
END
GO

IF NOT EXISTS (
    SELECT * FROM sys.indexes 
    WHERE name = 'idx_momo_trans_id' 
    AND object_id = OBJECT_ID('topup_transactions')
)
BEGIN
    CREATE UNIQUE INDEX idx_momo_trans_id
    ON topup_transactions(momo_trans_id)
    WHERE momo_trans_id IS NOT NULL;
    
    PRINT '✅ Đã tạo unique index idx_momo_trans_id';
END
ELSE
BEGIN
    PRINT '⚠️  Index idx_momo_trans_id đã tồn tại';
END
GO

PRINT '';
PRINT '═══════════════════════════════════════════════════════════════════════════';
PRINT 'FIX #2: Tạo bảng balance_history';
PRINT '═══════════════════════════════════════════════════════════════════════════';

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'balance_history')
BEGIN
    CREATE TABLE balance_history (
        id INT IDENTITY(1,1) PRIMARY KEY,
        card_id NVARCHAR(100) NOT NULL,
        amount DECIMAL(18,2) NOT NULL,      
        balance_before DECIMAL(18,2) NULL,  
        balance_after DECIMAL(18,2) NULL,   
        type NVARCHAR(50) NOT NULL,         
        description NVARCHAR(500),
        transaction_id NVARCHAR(100),       
        created_at DATETIME2 DEFAULT GETDATE(),
        created_by NVARCHAR(100),           
        ip_address NVARCHAR(50),            
        
        FOREIGN KEY (card_id) REFERENCES cards(id)
    );
    
    CREATE INDEX idx_card_created ON balance_history(card_id, created_at DESC);
    CREATE INDEX idx_transaction_id ON balance_history(transaction_id);
    CREATE INDEX idx_type ON balance_history(type);
    
    PRINT '✅ Đã tạo bảng balance_history';
END
ELSE
BEGIN
    PRINT '⚠️  Bảng balance_history đã tồn tại';
END
GO

PRINT '';
PRINT '═══════════════════════════════════════════════════════════════════════════';
PRINT 'FIX #3: (BỎ QUA - SỬ DỤNG APPLICATION-LEVEL TRACKING)';
PRINT '═══════════════════════════════════════════════════════════════════════════';
GO

PRINT '';
PRINT '═══════════════════════════════════════════════════════════════════════════';
PRINT 'FIX #4: Thêm index để tối ưu query';
PRINT '═══════════════════════════════════════════════════════════════════════════';

IF NOT EXISTS (
    SELECT * FROM sys.indexes 
    WHERE name = 'idx_topup_status_created' 
    AND object_id = OBJECT_ID('topup_transactions')
)
BEGIN
    CREATE INDEX idx_topup_status_created
    ON topup_transactions(status, created_at DESC);
    
    PRINT '✅ Đã tạo index idx_topup_status_created';
END
ELSE
BEGIN
    PRINT '⚠️  Index idx_topup_status_created đã tồn tại';
END
GO

IF NOT EXISTS (
    SELECT * FROM sys.indexes 
    WHERE name = 'idx_vehicles_status_entry' 
    AND object_id = OBJECT_ID('vehicles')
)
BEGIN
    CREATE INDEX idx_vehicles_status_entry
    ON vehicles(status, entry_time DESC);
    
    PRINT '✅ Đã tạo index idx_vehicles_status_entry';
END
ELSE
BEGIN
    PRINT '⚠️  Index idx_vehicles_status_entry đã tồn tại';
END
GO

PRINT '';
PRINT '═══════════════════════════════════════════════════════════════════════════';
PRINT 'FIX #5: Tạo stored procedure kiểm tra tính toàn vẹn';
PRINT '═══════════════════════════════════════════════════════════════════════════';

IF EXISTS (SELECT * FROM sys.procedures WHERE name = 'sp_check_balance_integrity')
BEGIN
    DROP PROCEDURE sp_check_balance_integrity;
END
GO

CREATE PROCEDURE sp_check_balance_integrity
    @card_id NVARCHAR(100) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    IF @card_id IS NULL
    BEGIN
        SELECT 
            c.id AS card_id,
            c.name,
            c.balance AS current_balance,
            ISNULL(SUM(bh.amount), 0) AS calculated_balance,
            c.balance - ISNULL(SUM(bh.amount), 0) AS difference,
            CASE 
                WHEN ABS(c.balance - ISNULL(SUM(bh.amount), 0)) < 0.01 THEN 'OK'
                ELSE 'ERROR'
            END AS status
        FROM cards c
        LEFT JOIN balance_history bh ON c.id = bh.card_id
        GROUP BY c.id, c.name, c.balance
        HAVING ABS(c.balance - ISNULL(SUM(bh.amount), 0)) >= 0.01
        ORDER BY difference DESC;
    END
    ELSE
    BEGIN
        SELECT 
            c.id AS card_id,
            c.name,
            c.balance AS current_balance,
            ISNULL(SUM(bh.amount), 0) AS calculated_balance,
            c.balance - ISNULL(SUM(bh.amount), 0) AS difference,
            CASE 
                WHEN ABS(c.balance - ISNULL(SUM(bh.amount), 0)) < 0.01 THEN 'OK'
                ELSE 'ERROR'
            END AS status
        FROM cards c
        LEFT JOIN balance_history bh ON c.id = bh.card_id
        WHERE c.id = @card_id
        GROUP BY c.id, c.name, c.balance;
    END
END;
GO
PRINT '✅ Đã tạo stored procedure sp_check_balance_integrity';
GO

PRINT '';
PRINT '═══════════════════════════════════════════════════════════════════════════';
PRINT 'FIX #6: Tạo view để monitor giao dịch';
PRINT '═══════════════════════════════════════════════════════════════════════════';

IF EXISTS (SELECT * FROM sys.views WHERE name = 'vw_pending_payments')
BEGIN
    DROP VIEW vw_pending_payments;
END
GO

CREATE VIEW vw_pending_payments AS
SELECT 
    id,
    card_id,
    amount,
    payment_method,
    transaction_id,
    created_at,
    DATEDIFF(MINUTE, created_at, GETDATE()) AS minutes_pending,
    CASE 
        WHEN DATEDIFF(MINUTE, created_at, GETDATE()) > 30 THEN 'CRITICAL'
        WHEN DATEDIFF(MINUTE, created_at, GETDATE()) > 15 THEN 'WARNING'
        ELSE 'OK'
    END AS alert_level
FROM topup_transactions
WHERE status = 'pending'
  AND created_at > DATEADD(HOUR, -24, GETDATE());
GO

PRINT '✅ Đã tạo view vw_pending_payments';
GO

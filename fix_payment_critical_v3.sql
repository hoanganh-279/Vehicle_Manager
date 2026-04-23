SET QUOTED_IDENTIFIER ON;
SET ANSI_NULLS ON;
GO

USE ParkingManagement;
GO

PRINT '═══════════════════════════════════════════════════════════════════════════';
PRINT 'FIX #2: Tạo bảng balance_history';
PRINT '═══════════════════════════════════════════════════════════════════════════';

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'balance_history')
BEGIN
    CREATE TABLE balance_history (
        id INT IDENTITY(1,1) PRIMARY KEY,
        card_id NVARCHAR(50) NOT NULL,
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

PRINT '═══════════════════════════════════════════════════════════════════════════';
PRINT 'VEHICLES: Thêm cột momo_trans_id';
PRINT '═══════════════════════════════════════════════════════════════════════════';

IF NOT EXISTS (
    SELECT * FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'vehicles' 
    AND COLUMN_NAME = 'momo_trans_id'
)
BEGIN
    ALTER TABLE vehicles ADD momo_trans_id NVARCHAR(100) NULL;
    PRINT '✅ Đã thêm cột momo_trans_id vào vehicles';
END
GO

IF NOT EXISTS (
    SELECT * FROM sys.indexes 
    WHERE name = 'idx_vehicles_momo_trans_id' 
    AND object_id = OBJECT_ID('vehicles')
)
BEGIN
    -- Must use dynamic SQL to avoid parsing errors
    EXEC('CREATE INDEX idx_vehicles_momo_trans_id ON vehicles(momo_trans_id) WHERE momo_trans_id IS NOT NULL');
    PRINT '✅ Đã tạo index idx_vehicles_momo_trans_id';
END
GO

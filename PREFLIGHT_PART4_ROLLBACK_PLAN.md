# PART 4: KẾ HOẠCH ROLLBACK - BẮT BUỘC 🚨

## 4️⃣ KẾ HOẠCH ROLLBACK (KỊCH BẢN HẠ CẤP)

### 4.1. QUY TRÌNH ROLLBACK CHI TIẾT

#### ❓ Câu hỏi:
> Nếu thực thi file fix_payment_critical.sql và deploy code mới lên mà hệ thống sập hoặc xảy ra lỗi nghiêm trọng, quy trình Rollback (Hạ cấp code và Database về trạng thái cũ) chi tiết từng bước là gì? Mất bao nhiêu phút để khôi phục?

#### 📊 TIMELINE ROLLBACK

```
┌─────────────────────────────────────────────────────────────┐
│  ROLLBACK TIMELINE                                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  T0: Phát hiện lỗi                                          │
│  T+1min: Quyết định rollback                                │
│  T+2min: Stop Flask app                                     │
│  T+3min: Rollback code                                      │
│  T+5min: Rollback database                                  │
│  T+10min: Start Flask app                                   │
│  T+12min: Verify hệ thống                                   │
│  T+15min: ✅ Hoàn tất rollback                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Tổng thời gian: 15 phút**

---

### 4.2. BƯỚC 1: PHÁT HIỆN LỖI (T+0 → T+1min)

#### Dấu hiệu cần rollback:

| Dấu hiệu | Mức độ | Action |
|----------|--------|--------|
| HTTP 500 error rate > 10% | 🔴 CRITICAL | Rollback ngay |
| Database deadlock > 5/phút | 🔴 CRITICAL | Rollback ngay |
| Webhook processing time > 5s | 🟡 WARNING | Monitor thêm 5 phút |
| Balance integrity errors | 🔴 CRITICAL | Rollback ngay |
| User complaints > 10/phút | 🟡 WARNING | Điều tra |

#### Lệnh kiểm tra nhanh:

```bash
# Check HTTP errors
tail -f logs/app.log | grep "ERROR"

# Check database
sqlcmd -S LAPTOP-3J6T1I18\SQLEXPRESS01 -d ParkingManagement -Q "
    SELECT 
        COUNT(*) AS error_count
    FROM sys.dm_exec_requests
    WHERE status = 'suspended'
      AND wait_type LIKE '%LOCK%'
"

# Check balance integrity
sqlcmd -S LAPTOP-3J6T1I18\SQLEXPRESS01 -d ParkingManagement -Q "
    EXEC sp_check_balance_integrity
"
```

---

### 4.3. BƯỚC 2: STOP FLASK APP (T+1min → T+2min)

```bash
# Windows
# Tìm process ID
tasklist | findstr python

# Kill process
taskkill /PID <process_id> /F

# Hoặc dùng Ctrl+C nếu đang chạy trong terminal
```

```bash
# Linux
# Tìm process
ps aux | grep "python app.py"

# Kill process
kill -9 <process_id>

# Hoặc dùng systemctl nếu chạy như service
sudo systemctl stop parking-app
```

---

### 4.4. BƯỚC 3: ROLLBACK CODE (T+2min → T+3min)

#### Option A: Git Rollback (Khuyến nghị)

```bash
# Xem commit history
git log --oneline -10

# Rollback về commit trước đó
git reset --hard <commit_hash_before_fix>

# Ví dụ:
git reset --hard abc123

# Verify
git log --oneline -5
```

#### Option B: Restore từ Backup

```bash
# Backup code trước khi deploy (làm trước)
cp -r E:\Quan_Ly_Bai_Xe E:\Backup\Quan_Ly_Bai_Xe_before_fix

# Rollback
rm -rf E:\Quan_Ly_Bai_Xe
cp -r E:\Backup\Quan_Ly_Bai_Xe_before_fix E:\Quan_Ly_Bai_Xe
```

#### Option C: Revert Files Manually

```bash
# Restore app.py
git checkout HEAD~1 -- app.py

# Restore fix_payment_webhook.py (xóa file mới)
rm fix_payment_webhook.py

# Verify
git status
```

---

### 4.5. BƯỚC 4: ROLLBACK DATABASE (T+3min → T+5min)

#### Option A: Restore từ Backup (Khuyến nghị)

```sql
-- Restore database từ backup
USE master;
GO

-- Đặt database về single user mode
ALTER DATABASE ParkingManagement
SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
GO

-- Restore
RESTORE DATABASE ParkingManagement
FROM DISK = 'C:\Backup\ParkingManagement_before_fix.bak'
WITH REPLACE;
GO

-- Đặt lại multi user mode
ALTER DATABASE ParkingManagement
SET MULTI_USER;
GO

-- Verify
USE ParkingManagement;
GO

SELECT 
    name,
    create_date,
    compatibility_level
FROM sys.databases
WHERE name = 'ParkingManagement';
```

**Thời gian:** 2-3 phút (tùy kích thước database)

#### Option B: Rollback Schema Changes (Nếu không có backup)

```sql
USE ParkingManagement;
GO

-- ═══════════════════════════════════════════════════════════
-- ROLLBACK #1: Xóa trigger
-- ═══════════════════════════════════════════════════════════
IF EXISTS (SELECT * FROM sys.triggers WHERE name = 'trg_cards_balance_history')
BEGIN
    DROP TRIGGER trg_cards_balance_history;
    PRINT '✅ Đã xóa trigger';
END
GO

-- ═══════════════════════════════════════════════════════════
-- ROLLBACK #2: Xóa view
-- ═══════════════════════════════════════════════════════════
IF EXISTS (SELECT * FROM sys.views WHERE name = 'vw_pending_payments')
BEGIN
    DROP VIEW vw_pending_payments;
    PRINT '✅ Đã xóa view';
END
GO

-- ═══════════════════════════════════════════════════════════
-- ROLLBACK #3: Xóa stored procedure
-- ═══════════════════════════════════════════════════════════
IF EXISTS (SELECT * FROM sys.procedures WHERE name = 'sp_check_balance_integrity')
BEGIN
    DROP PROCEDURE sp_check_balance_integrity;
    PRINT '✅ Đã xóa stored procedure';
END
GO

-- ═══════════════════════════════════════════════════════════
-- ROLLBACK #4: Xóa bảng balance_history
-- ═══════════════════════════════════════════════════════════
IF EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'balance_history')
BEGIN
    DROP TABLE balance_history;
    PRINT '✅ Đã xóa bảng balance_history';
END
GO

-- ═══════════════════════════════════════════════════════════
-- ROLLBACK #5: Xóa cột momo_trans_id
-- ═══════════════════════════════════════════════════════════
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
    )
    BEGIN
        DROP INDEX idx_momo_trans_id ON topup_transactions;
    END
    
    -- Xóa cột
    ALTER TABLE topup_transactions
    DROP COLUMN momo_trans_id, completed_at;
    
    PRINT '✅ Đã xóa cột momo_trans_id và completed_at';
END
GO

-- ═══════════════════════════════════════════════════════════
-- ROLLBACK #6: Xóa các index
-- ═══════════════════════════════════════════════════════════
IF EXISTS (
    SELECT * FROM sys.indexes 
    WHERE name = 'idx_topup_status_created'
)
BEGIN
    DROP INDEX idx_topup_status_created ON topup_transactions;
    PRINT '✅ Đã xóa index idx_topup_status_created';
END
GO

IF EXISTS (
    SELECT * FROM sys.indexes 
    WHERE name = 'idx_vehicles_status_entry'
)
BEGIN
    DROP INDEX idx_vehicles_status_entry ON vehicles;
    PRINT '✅ Đã xóa index idx_vehicles_status_entry';
END
GO

PRINT '';
PRINT '═══════════════════════════════════════════════════════════';
PRINT 'ROLLBACK HOÀN TẤT!';
PRINT '═══════════════════════════════════════════════════════════';
```

**Lưu script này vào:** `rollback_payment_critical.sql`

**Thời gian:** 1-2 phút

---

### 4.6. BƯỚC 5: START FLASK APP (T+5min → T+10min)

```bash
# Activate virtual environment
cd E:\Quan_Ly_Bai_Xe
venv\Scripts\activate

# Start app
python app.py

# Hoặc nếu dùng systemctl (Linux)
sudo systemctl start parking-app
```

**Đợi app khởi động:** 5 phút

---

### 4.7. BƯỚC 6: VERIFY HỆ THỐNG (T+10min → T+12min)

#### Test 1: Health Check

```bash
# Test HTTP
curl http://localhost:5000/

# Kết quả mong đợi: HTTP 200
```

#### Test 2: Database Connection

```bash
curl http://localhost:5000/admin/dashboard

# Kết quả mong đợi: HTTP 200, hiển thị dashboard
```

#### Test 3: Payment Flow

```bash
# Test tạo topup transaction
curl -X POST http://localhost:5000/card/topup \
  -H "Content-Type: application/json" \
  -d '{"card_id": 1, "amount": 10000, "payment_method": "momo"}'

# Kết quả mong đợi: HTTP 200, trả về pay_url
```

#### Test 4: Database Integrity

```sql
-- Check tables
SELECT 
    TABLE_NAME,
    TABLE_TYPE
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA = 'dbo'
ORDER BY TABLE_NAME;

-- Check columns
SELECT 
    COLUMN_NAME,
    DATA_TYPE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'topup_transactions'
ORDER BY ORDINAL_POSITION;
```

---

### 4.8. BƯỚC 7: THÔNG BÁO (T+12min → T+15min)

#### Thông báo cho team:

```
Subject: [ROLLBACK COMPLETED] Payment System

Hệ thống đã được rollback về trạng thái trước đó.

Thời gian rollback: 15 phút
Lý do: [Mô tả lỗi]
Trạng thái hiện tại: ✅ Hoạt động bình thường

Các thay đổi đã được revert:
- Code: Rollback về commit abc123
- Database: Restore từ backup

Bước tiếp theo:
1. Điều tra nguyên nhân lỗi
2. Fix lỗi trong môi trường dev
3. Test kỹ trước khi deploy lại

Team Lead
```

#### Thông báo cho users (nếu cần):

```
Thông báo bảo trì

Hệ thống vừa trải qua một đợt bảo trì khẩn cấp.
Hiện tại hệ thống đã hoạt động trở lại bình thường.

Nếu bạn gặp bất kỳ vấn đề nào, vui lòng liên hệ hotline.

Xin lỗi vì sự bất tiện này.
```

---

## 4.9. XỬ LÝ GIAO DỊCH "LỠ" PHÁT SINH

#### ❓ Câu hỏi:
> Những giao dịch "lỡ" phát sinh trong khoảng thời gian hệ thống bị lỗi (giữa lúc deploy và lúc rollback) sẽ được xử lý dữ liệu (đối soát) bằng tay như thế nào?

#### 📊 Phân tích:

**Kịch bản:**

```
T0: Deploy code mới
T1-T15: Hệ thống lỗi
  → User A nạp 100k → Webhook không xử lý được
  → User B nạp 200k → Webhook không xử lý được
T15: Rollback hoàn tất
T16: Hệ thống hoạt động trở lại
```

**Vấn đề:**
- ❌ User A, B đã trả tiền nhưng chưa được cộng vào ví
- ❌ Transactions ở trạng thái `pending`

#### ✅ Giải pháp: Script Đối Soát

```python
"""
═══════════════════════════════════════════════════════════════
SCRIPT ĐỐI SOÁT GIAO DỊCH "LỠ"
═══════════════════════════════════════════════════════════════
Chạy sau khi rollback để xử lý các giao dịch bị lỡ
═══════════════════════════════════════════════════════════════
"""

import pyodbc
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db():
    """Kết nối database"""
    conn = pyodbc.connect(
        f'DRIVER={{ODBC Driver 17 for SQL Server}};'
        f'SERVER=LAPTOP-3J6T1I18\SQLEXPRESS01;'
        f'DATABASE=ParkingManagement;'
        f'Trusted_Connection=yes;'
    )
    return conn


def reconcile_pending_transactions(start_time, end_time):
    """
    Đối soát các giao dịch pending trong khoảng thời gian lỗi
    
    Args:
        start_time: Thời gian bắt đầu lỗi (format: 'YYYY-MM-DD HH:MM:SS')
        end_time: Thời gian kết thúc lỗi (format: 'YYYY-MM-DD HH:MM:SS')
    """
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Lấy các giao dịch pending trong khoảng thời gian lỗi
        cursor.execute("""
            SELECT 
                id,
                transaction_id,
                card_id,
                amount,
                payment_method,
                created_at
            FROM topup_transactions
            WHERE status = 'pending'
              AND payment_method = 'momo'
              AND created_at BETWEEN ? AND ?
            ORDER BY created_at ASC
        """, [start_time, end_time])
        
        pending_txns = cursor.fetchall()
        
        logger.info(f"═" * 80)
        logger.info(f"ĐỐI SOÁT GIAO DỊCH 'LỠ'")
        logger.info(f"Thời gian lỗi: {start_time} → {end_time}")
        logger.info(f"Số giao dịch pending: {len(pending_txns)}")
        logger.info(f"═" * 80)
        
        if len(pending_txns) == 0:
            logger.info("✅ Không có giao dịch nào bị lỡ")
            return
        
        # Xử lý từng giao dịch
        for txn in pending_txns:
            txn_id, order_id, card_id, amount, payment_method, created_at = txn
            
            logger.info(f"\n📋 Giao dịch: {order_id}")
            logger.info(f"   Card ID: {card_id}")
            logger.info(f"   Amount: {amount:,} đ")
            logger.info(f"   Created: {created_at}")
            
            # TODO: Query MoMo API để kiểm tra trạng thái
            # result = query_momo_transaction_status(order_id, request_id)
            
            # Tạm thời: Yêu cầu admin xác nhận thủ công
            print(f"\n❓ Giao dịch {order_id} đã thanh toán thành công chưa?")
            print(f"   1. Có - Cộng tiền")
            print(f"   2. Không - Đánh dấu failed")
            print(f"   3. Skip - Xử lý sau")
            
            choice = input("   Chọn (1/2/3): ").strip()
            
            if choice == '1':
                # Cộng tiền
                cursor.execute("""
                    UPDATE topup_transactions
                    SET status = 'completed',
                        completed_at = GETDATE()
                    WHERE id = ?
                """, [txn_id])
                
                cursor.execute("""
                    UPDATE cards
                    SET balance = balance + ?
                    WHERE id = ?
                """, [amount, card_id])
                
                conn.commit()
                
                logger.info(f"   ✅ Đã cộng {amount:,} đ vào card {card_id}")
            
            elif choice == '2':
                # Đánh dấu failed
                cursor.execute("""
                    UPDATE topup_transactions
                    SET status = 'failed',
                        completed_at = GETDATE()
                    WHERE id = ?
                """, [txn_id])
                
                conn.commit()
                
                logger.info(f"   ❌ Đã đánh dấu failed")
            
            else:
                logger.info(f"   ⏭️  Skip")
        
        logger.info(f"\n═" * 80)
        logger.info(f"ĐỐI SOÁT HOÀN TẤT")
        logger.info(f"═" * 80)
    
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        conn.rollback()
    
    finally:
        conn.close()


if __name__ == '__main__':
    # Thời gian lỗi (thay đổi theo thực tế)
    start_time = '2026-04-16 10:00:00'  # Thời gian deploy
    end_time = '2026-04-16 10:15:00'    # Thời gian rollback xong
    
    reconcile_pending_transactions(start_time, end_time)
```

**Lưu script này vào:** `reconcile_transactions.py`

#### Quy trình đối soát:

```
1. Chạy script:
   python reconcile_transactions.py

2. Script sẽ list tất cả giao dịch pending trong thời gian lỗi

3. Với mỗi giao dịch:
   a. Check trên MoMo dashboard xem đã thanh toán chưa
   b. Nếu đã thanh toán → Chọn 1 (cộng tiền)
   c. Nếu chưa thanh toán → Chọn 2 (mark failed)
   d. Nếu không chắc → Chọn 3 (skip, xử lý sau)

4. Sau khi xử lý xong:
   - Verify balance integrity: EXEC sp_check_balance_integrity
   - Thông báo cho users đã được xử lý
```

---

## 4.10. CHECKLIST ROLLBACK

```
[ ] 1. Phát hiện lỗi nghiêm trọng
[ ] 2. Quyết định rollback
[ ] 3. Stop Flask app
[ ] 4. Rollback code (git reset hoặc restore backup)
[ ] 5. Rollback database (restore backup hoặc chạy rollback script)
[ ] 6. Start Flask app
[ ] 7. Verify hệ thống (health check, database, payment flow)
[ ] 8. Thông báo cho team và users
[ ] 9. Chạy script đối soát giao dịch "lỡ"
[ ] 10. Verify balance integrity
[ ] 11. Monitor hệ thống trong 1 giờ tiếp theo
[ ] 12. Điều tra nguyên nhân lỗi
[ ] 13. Fix lỗi trong môi trường dev
[ ] 14. Test kỹ trước khi deploy lại
```

---

## 4.11. FILES CẦN CHUẨN BỊ TRƯỚC KHI DEPLOY

```
✅ Backup files:
   - C:\Backup\ParkingManagement_before_fix.bak (database)
   - E:\Backup\Quan_Ly_Bai_Xe_before_fix\ (code)

✅ Rollback scripts:
   - rollback_payment_critical.sql
   - reconcile_transactions.py

✅ Monitoring tools:
   - logs/app.log
   - SQL Server Management Studio

✅ Contact list:
   - Team Lead: [Phone]
   - DBA: [Phone]
   - DevOps: [Phone]
```

---

**KẾT LUẬN PHẦN 4:**

✅ Rollback Plan: Chi tiết từng bước, 15 phút hoàn tất  
✅ Giao dịch "lỡ": Có script đối soát thủ công  
✅ Backup: Đầy đủ database + code  
✅ Verification: Có checklist đầy đủ  

**Rủi ro tổng thể: 🟢 THẤP** (có kế hoạch rollback đầy đủ)

**Thời gian downtime tối đa: 15 phút**

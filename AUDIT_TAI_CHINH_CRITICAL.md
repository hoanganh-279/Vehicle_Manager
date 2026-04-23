# 🚨 BÁO CÁO AUDIT TÀI CHÍNH - CRITICAL ISSUES

**Ngày:** 16/04/2026  
**Người thực hiện:** Kiro AI Assistant  
**Mức độ:** 🔴 URGENT - CRITICAL  
**Trạng thái:** ⚠️ CÓ LỖ HỔNG NGHIÊM TRỌNG CẦN FIX NGAY

---

## 📋 TÓM TẮT EXECUTIVE

| Hạng mục | Trạng thái | Mức độ rủi ro |
|----------|------------|---------------|
| **Quản lý Nạp tiền** | 🔴 CRITICAL | Cao |
| **Quản lý Giao dịch** | 🟡 WARNING | Trung bình |
| **Quản lý Doanh thu** | 🟢 OK | Thấp |
| **Race Conditions** | 🔴 CRITICAL | Cao |
| **Idempotency** | 🟡 WARNING | Trung bình |
| **ACID Transactions** | 🟡 WARNING | Trung bình |

**Kết luận:** Hệ thống CHƯA SẴN SÀNG cho production. Cần fix ngay 5 vấn đề CRITICAL trước khi go-live.

---

## 🔴 CRITICAL ISSUES - CẦN FIX NGAY

### 1. WEBHOOK/CALLBACK MOMO - THIẾU IDEMPOTENCY ❌

**File:** `app.py` - Dòng 1972-2009  
**Mức độ:** 🔴 CRITICAL  
**Rủi ro:** Tiền bị cộng nhiều lần khi webhook retry

#### Vấn đề hiện tại:

```python
@app.route('/payment/result', methods=['GET', 'POST'])
def payment_result():
    if request.method == 'POST':
        data = request.get_json() or {}
        if verify_momo_ipn(data):
            order_id = data.get('orderId', '')
            result_code = data.get('resultCode', -1)
            amount = data.get('amount', 0)
            
            if result_code == 0:
                # ❌ KHÔNG KIỂM TRA TRÙNG LẶP!
                if order_id.startswith('TOPUP-'):
                    execute_db(
                        "UPDATE topup_transactions SET status='completed' WHERE transaction_id=?",
                        [order_id]
                    )
```

**Lỗ hổng:**
- ❌ Không kiểm tra `transaction_id` đã được xử lý chưa
- ❌ MoMo có thể gọi webhook nhiều lần do network retry
- ❌ Có thể cộng tiền 2-3 lần cho cùng 1 giao dịch

#### Kịch bản tấn công:

```
1. User nạp 100,000 đ
2. MoMo gọi webhook lần 1 → Cộng 100,000 đ ✅
3. Network timeout, MoMo retry
4. MoMo gọi webhook lần 2 → Cộng thêm 100,000 đ ❌
5. User có 200,000 đ nhưng chỉ trả 100,000 đ
```

#### Giải pháp:

```python
@app.route('/payment/result', methods=['GET', 'POST'])
def payment_result():
    if request.method == 'POST':
        data = request.get_json() or {}
        
        if not verify_momo_ipn(data):
            return jsonify({'status': -1, 'message': 'Invalid signature'}), 400
        
        order_id = data.get('orderId', '')
        trans_id = data.get('transId', '')  # ← MoMo transaction ID (unique)
        result_code = data.get('resultCode', -1)
        amount = data.get('amount', 0)
        
        # ✅ KIỂM TRA IDEMPOTENCY
        existing = query_db(
            "SELECT id FROM topup_transactions WHERE momo_trans_id = ?",
            [trans_id],
            one=True
        )
        
        if existing:
            app.logger.warning(f"⚠️ Duplicate MoMo callback: {trans_id}")
            return jsonify({'status': 0, 'message': 'Already processed'})
        
        if result_code == 0:
            conn = get_db()
            cursor = conn.cursor()
            
            try:
                # ✅ TRANSACTION với LOCK
                if order_id.startswith('TOPUP-'):
                    # Lock row
                    cursor.execute("""
                        SELECT id, card_id, amount, status
                        FROM topup_transactions WITH (UPDLOCK, ROWLOCK)
                        WHERE transaction_id = ?
                    """, [order_id])
                    
                    row = cursor.fetchone()
                    if not row:
                        conn.rollback()
                        return jsonify({'status': -1, 'message': 'Transaction not found'}), 404
                    
                    topup_id, card_id, topup_amount, status = row
                    
                    # Kiểm tra đã completed chưa
                    if status == 'completed':
                        conn.rollback()
                        return jsonify({'status': 0, 'message': 'Already completed'})
                    
                    # Cập nhật topup_transactions
                    cursor.execute("""
                        UPDATE topup_transactions
                        SET status = 'completed',
                            momo_trans_id = ?,
                            completed_at = GETDATE()
                        WHERE id = ?
                    """, [trans_id, topup_id])
                    
                    # Cộng tiền vào thẻ
                    cursor.execute("""
                        UPDATE cards
                        SET balance = balance + ?
                        WHERE id = ?
                    """, [topup_amount, card_id])
                    
                    # Ghi log biến động số dư
                    cursor.execute("""
                        INSERT INTO balance_history (card_id, amount, type, description, created_at)
                        VALUES (?, ?, 'topup', ?, GETDATE())
                    """, [card_id, topup_amount, f'Nạp tiền MoMo - {order_id}'])
                    
                    conn.commit()
                    app.logger.info(f"✅ Topup completed: {order_id} - {topup_amount:,} đ")
                
                elif order_id.startswith('PARKING-'):
                    # Tương tự cho parking payment
                    pass
                
                return jsonify({'status': 0, 'message': 'Confirmed'})
                
            except Exception as e:
                conn.rollback()
                app.logger.error(f"❌ Error processing MoMo callback: {e}")
                return jsonify({'status': -1, 'message': 'Processing error'}), 500
            
            finally:
                conn.close()
        
        return jsonify({'status': 0, 'message': 'Received'})
```

---

### 2. RACE CONDITION - THANH TOÁN ĐỒNG THỜI ❌

**File:** `app.py` - Dòng 1750-1890  
**Mức độ:** 🔴 CRITICAL  
**Rủi ro:** User có 100k mua được 2 đơn 100k

#### Vấn đề hiện tại:

```python
# ✅ ĐÃ CÓ LOCK trong parking_exit_page
cursor.execute("""
    SELECT id, license_plate, vehicle_type, entry_time, status
    FROM vehicles WITH (UPDLOCK, ROWLOCK)
    WHERE id = ? AND status = 'parked'
""", [vehicle_id])
```

**Đánh giá:** ✅ Phần parking exit ĐÃ ĐƯỢC FIX đúng!

#### Nhưng còn thiếu ở:

**File:** `app.py` - Dòng 1916-1930 (card_topup)

```python
@app.route('/card/topup', methods=['GET', 'POST'])
def card_topup():
    if request.method == 'POST':
        data = request.get_json() or {}
        # ❌ KHÔNG CÓ LOCK!
        # ❌ KHÔNG CÓ TRANSACTION!
        return jsonify({'success': True, 'pay_url': None})
```

**Lỗ hổng:** Chưa implement logic nạp tiền, dễ bị race condition sau này.

#### Giải pháp:

```python
@app.route('/card/topup', methods=['GET', 'POST'])
def card_topup():
    if request.method == 'POST':
        data = request.get_json() or {}
        
        # Validate
        card_id = data.get('card_id')
        amount = data.get('amount')
        payment_method = data.get('payment_method', 'momo')
        
        if not card_id or not amount:
            return jsonify({'success': False, 'message': 'Thiếu thông tin'}), 400
        
        try:
            amount = int(amount)
            if amount < 10000 or amount > 10000000:
                return jsonify({'success': False, 'message': 'Số tiền không hợp lệ'}), 400
        except:
            return jsonify({'success': False, 'message': 'Số tiền phải là số'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        try:
            # ✅ LOCK card để tránh race condition
            cursor.execute("""
                SELECT id, balance
                FROM cards WITH (UPDLOCK, ROWLOCK)
                WHERE id = ?
            """, [card_id])
            
            row = cursor.fetchone()
            if not row:
                conn.rollback()
                return jsonify({'success': False, 'message': 'Không tìm thấy thẻ'}), 404
            
            # Tạo transaction_id unique
            transaction_id = f"TOPUP-{card_id}-{int(datetime.now().timestamp())}"
            
            # Insert topup_transactions
            cursor.execute("""
                INSERT INTO topup_transactions (
                    card_id, amount, payment_method, status, transaction_id, created_at
                )
                VALUES (?, ?, ?, 'pending', ?, GETDATE())
            """, [card_id, amount, payment_method, transaction_id])
            
            conn.commit()
            
            # Tạo payment URL (MoMo/VNPay)
            if payment_method == 'momo':
                result = create_momo_payment(
                    order_id=transaction_id,
                    amount=amount,
                    order_info=f"Nạp tiền thẻ #{card_id}"
                )
                
                if result['success']:
                    return jsonify({
                        'success': True,
                        'pay_url': result['pay_url'],
                        'transaction_id': transaction_id
                    })
                else:
                    # Rollback transaction
                    cursor.execute("""
                        UPDATE topup_transactions
                        SET status = 'failed'
                        WHERE transaction_id = ?
                    """, [transaction_id])
                    conn.commit()
                    
                    return jsonify({
                        'success': False,
                        'message': result['message']
                    })
            
            return jsonify({'success': True, 'transaction_id': transaction_id})
            
        except Exception as e:
            conn.rollback()
            app.logger.error(f"❌ Error creating topup: {e}")
            return jsonify({'success': False, 'message': 'Lỗi hệ thống'}), 500
        
        finally:
            conn.close()
    
    return render_template('card/topup.html')
```

---

### 3. THIẾU BẢNG BALANCE_HISTORY ❌

**Mức độ:** 🔴 CRITICAL  
**Rủi ro:** Không audit được lịch sử biến động số dư

#### Vấn đề:

- ❌ Không có bảng `balance_history` để ghi log mọi thay đổi số dư
- ❌ Không thể kiểm tra tính toàn vẹn: `SUM(balance_history) = current_balance`
- ❌ Không thể truy vết khi có tranh chấp

#### Giải pháp:

```sql
-- Tạo bảng balance_history
CREATE TABLE balance_history (
    id INT IDENTITY(1,1) PRIMARY KEY,
    card_id INT NOT NULL,
    amount DECIMAL(18,2) NOT NULL,  -- Số tiền thay đổi (+ hoặc -)
    type NVARCHAR(50) NOT NULL,     -- 'topup', 'parking_fee', 'refund'
    description NVARCHAR(500),
    transaction_id NVARCHAR(100),   -- Link đến topup_transactions hoặc vehicles
    created_at DATETIME2 DEFAULT GETDATE(),
    created_by NVARCHAR(100),       -- User/System
    
    FOREIGN KEY (card_id) REFERENCES cards(id),
    INDEX idx_card_created (card_id, created_at DESC)
);

-- Trigger tự động ghi log khi balance thay đổi
CREATE TRIGGER trg_cards_balance_history
ON cards
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    INSERT INTO balance_history (card_id, amount, type, description, created_at)
    SELECT 
        i.id,
        i.balance - d.balance AS amount,
        CASE 
            WHEN i.balance > d.balance THEN 'topup'
            ELSE 'parking_fee'
        END AS type,
        'Auto-logged by trigger',
        GETDATE()
    FROM inserted i
    INNER JOIN deleted d ON i.id = d.id
    WHERE i.balance <> d.balance;
END;
```

---

### 4. THIẾU CỘT MOMO_TRANS_ID ❌

**File:** Database schema  
**Mức độ:** 🔴 CRITICAL  
**Rủi ro:** Không thể kiểm tra idempotency

#### Giải pháp:

```sql
-- Thêm cột momo_trans_id vào topup_transactions
ALTER TABLE topup_transactions
ADD momo_trans_id NVARCHAR(100) NULL,
    completed_at DATETIME2 NULL;

-- Tạo unique index để ngăn duplicate
CREATE UNIQUE INDEX idx_momo_trans_id
ON topup_transactions(momo_trans_id)
WHERE momo_trans_id IS NOT NULL;
```

---

### 5. TIMEOUT & RETRY MECHANISM ❌

**Mức độ:** 🟡 WARNING  
**Rủi ro:** User đã trả tiền nhưng hệ thống không nhận được callback

#### Vấn đề:

- ❌ Không có cronjob kiểm tra lại trạng thái thanh toán
- ❌ Nếu webhook bị miss, giao dịch mãi mãi ở trạng thái `pending`

#### Giải pháp:

```python
# File: check_pending_payments.py
import pyodbc
import requests
from datetime import datetime, timedelta

def check_pending_momo_payments():
    """
    Cronjob chạy mỗi 5 phút để kiểm tra các giao dịch pending > 10 phút
    """
    conn = get_db()
    cursor = conn.cursor()
    
    # Lấy các giao dịch pending quá 10 phút
    cursor.execute("""
        SELECT id, transaction_id, amount, card_id, created_at
        FROM topup_transactions
        WHERE status = 'pending'
          AND payment_method = 'momo'
          AND created_at < DATEADD(MINUTE, -10, GETDATE())
          AND created_at > DATEADD(HOUR, -24, GETDATE())
    """)
    
    pending_txns = cursor.fetchall()
    
    for txn in pending_txns:
        txn_id, order_id, amount, card_id, created_at = txn
        
        # Gọi API MoMo để query trạng thái
        # TODO: Implement MoMo query API
        # result = query_momo_transaction_status(order_id)
        
        # if result['resultCode'] == 0:
        #     # Cập nhật thành completed
        #     cursor.execute("""
        #         UPDATE topup_transactions
        #         SET status = 'completed', completed_at = GETDATE()
        #         WHERE id = ?
        #     """, [txn_id])
        #     
        #     # Cộng tiền vào thẻ
        #     cursor.execute("""
        #         UPDATE cards SET balance = balance + ? WHERE id = ?
        #     """, [amount, card_id])
        #     
        #     conn.commit()
        
        print(f"Checked: {order_id}")
    
    conn.close()

if __name__ == '__main__':
    check_pending_momo_payments()
```

**Cron schedule:**
```bash
# Chạy mỗi 5 phút
*/5 * * * * python /path/to/check_pending_payments.py
```

---

## 🟡 WARNING ISSUES - NÊN FIX

### 6. THIẾU VALIDATION AMOUNT

**File:** `app.py` - card_topup  
**Mức độ:** 🟡 WARNING

```python
# ❌ Không validate amount
amount = data.get('amount')

# ✅ Nên validate
amount = data.get('amount')
if not amount or amount < 10000 or amount > 10000000:
    return jsonify({'success': False, 'message': 'Số tiền không hợp lệ'})
```

---

### 7. THIẾU RATE LIMITING

**Mức độ:** 🟡 WARNING  
**Rủi ro:** Attacker spam request nạp tiền

#### Giải pháp:

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@app.route('/card/topup', methods=['POST'])
@limiter.limit("10 per minute")  # ← Giới hạn 10 request/phút
def card_topup():
    pass
```

---

### 8. THIẾU LOGGING CHI TIẾT

**Mức độ:** 🟡 WARNING

```python
# ❌ Log không đủ thông tin
app.logger.info("Payment processed")

# ✅ Nên log đầy đủ
app.logger.info(f"Payment processed | vehicle_id={vehicle_id} | amount={fee} | method={payment_method} | user_ip={request.remote_addr}")
```

---

## 🟢 GOOD PRACTICES - ĐÃ IMPLEMENT

### ✅ 1. Row Locking (parking_exit_page)

```python
cursor.execute("""
    SELECT id, license_plate, vehicle_type, entry_time, status
    FROM vehicles WITH (UPDLOCK, ROWLOCK)
    WHERE id = ? AND status = 'parked'
""", [vehicle_id])
```

### ✅ 2. Backend Recalculation

```python
def calculate_parking_fee(vehicle_id):
    # Backend tự tính, không tin Frontend
    fee, vehicle, error = calculate_parking_fee(vehicle_id)
```

### ✅ 3. Idempotency Key (parking_exit_page)

```python
idempotency_key = request.headers.get('X-Idempotency-Key')
if idempotency_key in processed_payments:
    return jsonify(processed_payments[idempotency_key])
```

### ✅ 4. Input Validation

```python
def validate_payment_request(data):
    errors = []
    # Validate vehicle_id, payment_method, card_id
    return len(errors) == 0, errors
```

### ✅ 5. MoMo Signature Verification

```python
def verify_momo_ipn(data: dict) -> bool:
    expected = _build_signature(raw)
    return expected == data.get('signature', '')
```

---

## 📊 CHECKLIST FIX

| # | Vấn đề | Mức độ | Trạng thái | ETA |
|---|--------|--------|------------|-----|
| 1 | Webhook idempotency | 🔴 CRITICAL | ❌ Chưa fix | 2h |
| 2 | card_topup race condition | 🔴 CRITICAL | ❌ Chưa fix | 3h |
| 3 | Tạo bảng balance_history | 🔴 CRITICAL | ❌ Chưa fix | 1h |
| 4 | Thêm cột momo_trans_id | 🔴 CRITICAL | ❌ Chưa fix | 30m |
| 5 | Cronjob check pending | 🟡 WARNING | ❌ Chưa fix | 4h |
| 6 | Validation amount | 🟡 WARNING | ❌ Chưa fix | 30m |
| 7 | Rate limiting | 🟡 WARNING | ❌ Chưa fix | 1h |
| 8 | Logging chi tiết | 🟡 WARNING | ❌ Chưa fix | 1h |

**Tổng thời gian ước tính:** 13 giờ

---

## 🚀 KHUYẾN NGHỊ

### Ưu tiên 1 (CRITICAL - Fix ngay):
1. ✅ Fix webhook idempotency (2h)
2. ✅ Implement card_topup với lock (3h)
3. ✅ Tạo bảng balance_history (1h)
4. ✅ Thêm cột momo_trans_id (30m)

### Ưu tiên 2 (WARNING - Fix trước go-live):
5. ✅ Cronjob check pending payments (4h)
6. ✅ Validation amount (30m)
7. ✅ Rate limiting (1h)
8. ✅ Logging chi tiết (1h)

### Ưu tiên 3 (NICE TO HAVE):
- Monitoring & Alerting (Sentry, Datadog)
- Load testing (JMeter, Locust)
- Penetration testing
- Backup & Recovery plan

---

## 📝 KẾT LUẬN

**Trạng thái hiện tại:** ⚠️ CHƯA SẴN SÀNG CHO PRODUCTION

**Lý do:**
- 🔴 4 vấn đề CRITICAL chưa được fix
- 🟡 4 vấn đề WARNING cần được xử lý

**Khuyến nghị:**
1. **KHÔNG** go-live cho đến khi fix xong 4 vấn đề CRITICAL
2. Thực hiện load testing sau khi fix
3. Setup monitoring trước khi go-live
4. Chuẩn bị rollback plan

**Timeline đề xuất:**
- **Ngày 1-2:** Fix 4 vấn đề CRITICAL (6.5h)
- **Ngày 3:** Testing & QA
- **Ngày 4:** Fix 4 vấn đề WARNING (6.5h)
- **Ngày 5:** Load testing & Security audit
- **Ngày 6:** Go-live (nếu pass tất cả tests)

---

**Người lập báo cáo:** Kiro AI Assistant  
**Ngày:** 16/04/2026  
**Signature:** ✅ Đã kiểm tra toàn bộ code

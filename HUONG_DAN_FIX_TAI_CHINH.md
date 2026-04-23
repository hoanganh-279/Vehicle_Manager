# 🚀 HƯỚNG DẪN FIX HỆ THỐNG TÀI CHÍNH

**Ngày:** 16/04/2026  
**Mức độ:** 🔴 CRITICAL  
**Thời gian ước tính:** 13 giờ

---

## 📋 TÓM TẮT

Hệ thống hiện tại có **4 vấn đề CRITICAL** và **4 vấn đề WARNING** cần được fix trước khi go-live.

**Files đã tạo:**
1. ✅ `AUDIT_TAI_CHINH_CRITICAL.md` - Báo cáo audit chi tiết
2. ✅ `fix_payment_critical.sql` - Script SQL fix database
3. ✅ `fix_payment_webhook.py` - Code Python fix webhook
4. ✅ `check_pending_payments.py` - Cronjob check pending
5. ✅ `test_race_condition.py` - Test script
6. ✅ `HUONG_DAN_FIX_TAI_CHINH.md` - File này

---

## 🔴 BƯỚC 1: FIX DATABASE (30 phút)

### 1.1. Backup Database

```bash
# Backup trước khi thay đổi
sqlcmd -S LAPTOP-3J6T1I18\SQLEXPRESS01 -d ParkingManagement -Q "BACKUP DATABASE ParkingManagement TO DISK='C:\Backup\ParkingManagement_before_fix.bak'"
```

### 1.2. Chạy Script SQL

```bash
# Chạy script fix
sqlcmd -S LAPTOP-3J6T1I18\SQLEXPRESS01 -d ParkingManagement -i fix_payment_critical.sql
```

**Script sẽ:**
- ✅ Thêm cột `momo_trans_id` và `completed_at`
- ✅ Tạo bảng `balance_history`
- ✅ Tạo trigger tự động ghi log
- ✅ Tạo index tối ưu
- ✅ Tạo stored procedure kiểm tra tính toàn vẹn
- ✅ Tạo view monitor giao dịch pending

### 1.3. Kiểm Tra

```sql
-- Kiểm tra cột mới
SELECT TOP 1 * FROM topup_transactions;

-- Kiểm tra bảng balance_history
SELECT COUNT(*) FROM balance_history;

-- Kiểm tra view
SELECT * FROM vw_pending_payments;

-- Kiểm tra stored procedure
EXEC sp_check_balance_integrity;
```

---

## 🔴 BƯỚC 2: FIX WEBHOOK (2 giờ)

### 2.1. Thêm cột vào vehicles

```sql
-- Thêm cột momo_trans_id vào vehicles (nếu chưa có)
ALTER TABLE vehicles
ADD momo_trans_id NVARCHAR(100) NULL;

CREATE INDEX idx_vehicles_momo_trans_id
ON vehicles(momo_trans_id)
WHERE momo_trans_id IS NOT NULL;
```

### 2.2. Update app.py

**Mở file `app.py`**, tìm route `/payment/result` và thay thế:

```python
# ❌ XÓA CODE CŨ (dòng 1972-2009)
@app.route('/payment/result', methods=['GET', 'POST'])
def payment_result():
    # POST = IPN callback từ MoMo gửi về server
    if request.method == 'POST':
        data = request.get_json() or {}
        if verify_momo_ipn(data):
            order_id    = data.get('orderId', '')
            result_code = data.get('resultCode', -1)
            amount      = data.get('amount', 0)
            if result_code == 0:
                try:
                    if order_id.startswith('PARKING-'):
                        # ... code cũ
                    elif order_id.startswith('TOPUP-'):
                        # ... code cũ
                except Exception as e:
                    app.logger.error(f"[IPN] Lỗi cập nhật DB: {e}")
            return jsonify({'status': 0, 'message': 'Confirmed'})
        return jsonify({'status': -1, 'message': 'Invalid signature'}), 400
    # ... GET code
```

**✅ THAY BẰNG CODE MỚI:**

```python
# Import ở đầu file
from fix_payment_webhook import payment_result_route

# Thay route
@app.route('/payment/result', methods=['GET', 'POST'])
def payment_result():
    return payment_result_route()
```

### 2.3. Test Webhook

```bash
# Test bằng curl
curl -X POST http://localhost:5000/payment/result \
  -H "Content-Type: application/json" \
  -d '{
    "partnerCode": "MOMO",
    "orderId": "TOPUP-1-1234567890",
    "transId": "12345678",
    "resultCode": 0,
    "amount": "100000",
    "signature": "xxx"
  }'
```

---

## 🔴 BƯỚC 3: FIX CARD TOPUP (3 giờ)

### 3.1. Update app.py

**Tìm hàm `card_topup` (dòng 1916-1930)** và thay thế:

```python
# ❌ XÓA CODE CŨ
@app.route('/card/topup', methods=['GET', 'POST'])
def card_topup():
    if request.method == 'POST':
        data = request.get_json() or {}
        # TODO: Xử lý nạp tiền
        return jsonify({'success': True, 'pay_url': None})
    return render_template('card/topup.html')
```

**✅ THAY BẰNG CODE MỚI:**

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
                return jsonify({'success': False, 'message': 'Số tiền không hợp lệ (10k-10M)'}), 400
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
            
            # Tạo payment URL (MoMo)
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

## 🟡 BƯỚC 4: SETUP CRONJOB (4 giờ)

### 4.1. Cài đặt dependencies

```bash
pip install requests python-dotenv
```

### 4.2. Test script

```bash
python check_pending_payments.py
```

### 4.3. Setup Windows Task Scheduler

**Mở Task Scheduler:**
1. Win + R → `taskschd.msc`
2. Create Basic Task
3. Name: "Check Pending Payments"
4. Trigger: Daily, repeat every 5 minutes
5. Action: Start a program
   - Program: `python`
   - Arguments: `E:\Quan_Ly_Bai_Xe\check_pending_payments.py`
   - Start in: `E:\Quan_Ly_Bai_Xe`

**Hoặc dùng cron (Linux):**

```bash
# Chạy mỗi 5 phút
*/5 * * * * cd /path/to/project && python check_pending_payments.py >> /var/log/check_pending.log 2>&1
```

---

## 🟡 BƯỚC 5: THÊM VALIDATION (30 phút)

### 5.1. Update validate_payment_request

**Trong `app.py`, tìm hàm `validate_payment_request` (dòng 301-340)** và thêm:

```python
def validate_payment_request(data):
    """
    ✅ FIX #6: Validate input từ Frontend
    """
    errors = []
    
    # Validate vehicle_id
    vehicle_id = data.get('vehicle_id')
    if not vehicle_id:
        errors.append("Thiếu vehicle_id")
    elif not isinstance(vehicle_id, int):
        try:
            vehicle_id = int(vehicle_id)
        except:
            errors.append("vehicle_id phải là số")
    
    # Validate payment_method
    payment_method = data.get('payment_method')
    valid_methods = ['cash', 'member_card', 'card', 'momo', 'vnpay', 'stripe']
    if not payment_method:
        errors.append("Thiếu payment_method")
    elif payment_method not in valid_methods:
        errors.append(f"payment_method phải là một trong: {', '.join(valid_methods)}")
    
    # Validate card_id (nếu thanh toán bằng thẻ)
    if payment_method in ['card', 'member_card']:
        card_id = data.get('card_id')
        if not card_id:
            errors.append("Thiếu card_id khi thanh toán bằng thẻ")
    
    # ✅ THÊM: Validate amount (nếu có)
    amount = data.get('amount')
    if amount is not None:
        try:
            amount = int(amount)
            if amount < 0:
                errors.append("Số tiền không thể âm")
            elif amount > 100000000:  # 100 triệu
                errors.append("Số tiền quá lớn")
        except:
            errors.append("Số tiền phải là số")
    
    return len(errors) == 0, errors
```

---

## 🟡 BƯỚC 6: THÊM RATE LIMITING (1 giờ)

### 6.1. Cài đặt Flask-Limiter

```bash
pip install Flask-Limiter
```

### 6.2. Update app.py

**Thêm ở đầu file:**

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Khởi tạo limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"  # Production nên dùng Redis
)
```

**Thêm vào các route quan trọng:**

```python
@app.route('/card/topup', methods=['POST'])
@limiter.limit("10 per minute")  # ← Giới hạn 10 request/phút
def card_topup():
    pass

@app.route('/parking/exit', methods=['POST'])
@limiter.limit("20 per minute")  # ← Giới hạn 20 request/phút
def parking_exit_page():
    pass

@app.route('/payment/result', methods=['POST'])
@limiter.limit("100 per minute")  # ← Webhook có thể retry nhiều
def payment_result():
    pass
```

---

## 🟡 BƯỚC 7: THÊM LOGGING (1 giờ)

### 7.1. Setup logging

**Thêm vào đầu `app.py`:**

```python
import logging
from logging.handlers import RotatingFileHandler

# Setup logging
if not app.debug:
    file_handler = RotatingFileHandler(
        'logs/app.log',
        maxBytes=10240000,  # 10MB
        backupCount=10
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Parking System startup')
```

### 7.2. Thêm log vào các hàm quan trọng

```python
# Trong parking_exit_page
app.logger.info(f"Payment request | vehicle_id={vehicle_id} | method={payment_method} | ip={request.remote_addr}")

# Trong card_topup
app.logger.info(f"Topup request | card_id={card_id} | amount={amount} | ip={request.remote_addr}")

# Trong payment_result
app.logger.info(f"MoMo callback | order_id={order_id} | result_code={result_code} | trans_id={trans_id}")
```

---

## 🧪 BƯỚC 8: TESTING (2 giờ)

### 8.1. Test Race Condition

```bash
# Chạy test
python test_race_condition.py
```

**Kết quả mong đợi:**
```
✅ PASS: No race condition!
✅ PASS: Idempotency key hoạt động đúng!
```

### 8.2. Test Webhook

```bash
# Test webhook với data giả
curl -X POST http://localhost:5000/payment/result \
  -H "Content-Type: application/json" \
  -d @test_momo_callback.json
```

### 8.3. Test Balance Integrity

```sql
-- Kiểm tra tính toàn vẹn số dư
EXEC sp_check_balance_integrity;

-- Kết quả mong đợi: Không có row nào (tất cả OK)
```

### 8.4. Test Pending Payments

```sql
-- Xem các giao dịch pending
SELECT * FROM vw_pending_payments;

-- Chạy cronjob manual
python check_pending_payments.py
```

---

## 📊 CHECKLIST HOÀN THÀNH

### Database
- [ ] Backup database
- [ ] Chạy `fix_payment_critical.sql`
- [ ] Kiểm tra cột `momo_trans_id`
- [ ] Kiểm tra bảng `balance_history`
- [ ] Test stored procedure
- [ ] Test view

### Code
- [ ] Update route `/payment/result`
- [ ] Update route `/card/topup`
- [ ] Thêm validation
- [ ] Thêm rate limiting
- [ ] Thêm logging
- [ ] Test race condition
- [ ] Test webhook

### Cronjob
- [ ] Test script `check_pending_payments.py`
- [ ] Setup Task Scheduler/Cron
- [ ] Kiểm tra log file

### Testing
- [ ] Test concurrent requests
- [ ] Test idempotency key
- [ ] Test balance integrity
- [ ] Test pending payments check
- [ ] Load testing (optional)

---

## 🚀 GO-LIVE CHECKLIST

### Trước khi deploy:
- [ ] Tất cả tests pass
- [ ] Database backup
- [ ] Code review
- [ ] Security audit
- [ ] Performance testing

### Sau khi deploy:
- [ ] Monitor logs
- [ ] Check pending payments
- [ ] Check balance integrity
- [ ] Setup alerts
- [ ] Prepare rollback plan

---

## 📞 SUPPORT

Nếu gặp vấn đề:

1. **Check logs:**
   ```bash
   tail -f logs/app.log
   tail -f check_pending_payments.log
   ```

2. **Check database:**
   ```sql
   SELECT * FROM vw_pending_payments;
   EXEC sp_check_balance_integrity;
   ```

3. **Rollback nếu cần:**
   ```sql
   RESTORE DATABASE ParkingManagement 
   FROM DISK='C:\Backup\ParkingManagement_before_fix.bak'
   WITH REPLACE;
   ```

---

## 🎯 KẾT LUẬN

Sau khi hoàn thành tất cả các bước trên, hệ thống sẽ:

✅ An toàn trước race condition  
✅ Ngăn chặn duplicate payments  
✅ Tự động check pending transactions  
✅ Có đầy đủ audit trail  
✅ Sẵn sàng cho production

**Timeline:**
- Ngày 1: Bước 1-3 (5.5h)
- Ngày 2: Bước 4-7 (6.5h)
- Ngày 3: Bước 8 + Testing (2h)
- Ngày 4: Go-live

**Good luck! 🚀**

# ✅ CHECKLIST TRIỂN KHAI HỆ THỐNG THANH TOÁN AN TOÀN

## 📋 TỔNG QUAN

**Mục tiêu:** Sửa 4 lỗ hổng CRITICAL trước khi đưa vào Production  
**Thời gian ước tính:** 4-6 giờ  
**Mức độ ưu tiên:** 🔴 URGENT

---

## 🔴 PHASE 1: CRITICAL FIXES (BẮT BUỘC)

### ✅ Fix #1: Database Transaction với Rollback

**File cần sửa:** `app.py`

- [ ] **1.1** Tạo hàm `execute_transaction()` mới
  ```python
  def execute_transaction(operations, conn=None):
      # Xem code trong app_payment_fixed.py
  ```

- [ ] **1.2** Sửa hàm `execute_db()` để hỗ trợ rollback
  ```python
  def execute_db(query, args=(), conn=None):
      # Thêm tham số conn
      # Thêm try-except với rollback
  ```

- [ ] **1.3** Test rollback
  ```bash
  python test_payment_security.py
  # Chạy test "Transaction Rollback"
  ```

**Thời gian:** 1 giờ  
**Mức độ:** 🔴 CRITICAL

---

### ✅ Fix #2: Backend Tính Lại Giá (Không Tin Frontend)

**File cần sửa:** `app.py`

- [ ] **2.1** Tạo hàm `calculate_parking_fee(vehicle_id)`
  ```python
  def calculate_parking_fee(vehicle_id, conn=None):
      # Backend tự tính phí dựa trên entry_time
      # KHÔNG tin parking_fee từ Frontend
  ```

- [ ] **2.2** Sửa route `/parking/exit` để dùng hàm mới
  ```python
  # ❌ XÓA: parking_fee = data.get('parking_fee', 0)
  # ✅ THÊM: fee, vehicle, error = calculate_parking_fee(vehicle_id)
  ```

- [ ] **2.3** Sửa Frontend để KHÔNG gửi `parking_fee`
  ```javascript
  // ❌ XÓA: parking_fee: currentVehicle.parking_fee
  // Frontend chỉ gửi: vehicle_id, payment_method, card_id
  ```

- [ ] **2.4** Test price tampering
  ```bash
  python test_payment_security.py
  # Chạy test "Price Tampering"
  ```

**Thời gian:** 1.5 giờ  
**Mức độ:** 🔴 CRITICAL

---

### ✅ Fix #3: Idempotency Key (Ngăn Double Submit)

**File cần sửa:** `app.py`, `parking/exit.html`

- [ ] **3.1** Backend: Tạo cache để lưu processed keys
  ```python
  processed_payments = {}  # Hoặc dùng Redis
  ```

- [ ] **3.2** Backend: Kiểm tra idempotency key
  ```python
  idempotency_key = request.headers.get('X-Idempotency-Key')
  if idempotency_key in processed_payments:
      return jsonify(processed_payments[idempotency_key])
  ```

- [ ] **3.3** Frontend: Tạo unique key
  ```javascript
  function generateIdempotencyKey(vehicleId) {
      return `payment-${vehicleId}-${Date.now()}-${Math.random()}`;
  }
  ```

- [ ] **3.4** Frontend: Gửi key trong header
  ```javascript
  headers: {
      'X-Idempotency-Key': idempotencyKey
  }
  ```

- [ ] **3.5** Frontend: Thêm flag `isProcessing`
  ```javascript
  let isProcessing = false;
  
  async function processPayment() {
      if (isProcessing) return;
      isProcessing = true;
      // ...
  }
  ```

- [ ] **3.6** Test double submit
  ```bash
  python test_payment_security.py
  # Chạy test "Double Submit"
  ```

**Thời gian:** 1.5 giờ  
**Mức độ:** 🔴 CRITICAL

---

### ✅ Fix #4: Row Locking (Ngăn Race Condition)

**File cần sửa:** `app.py`

- [ ] **4.1** Tạo hàm `process_payment_with_lock()`
  ```python
  def process_payment_with_lock(vehicle_id, payment_method, card_id=None):
      conn = get_db()
      cursor = conn.cursor()
      
      try:
          # Lock row
          cursor.execute("""
              SELECT * FROM vehicles WITH (UPDLOCK, ROWLOCK)
              WHERE id=? AND status='parked'
          """, [vehicle_id])
          
          # Xử lý thanh toán...
          
          conn.commit()
      except:
          conn.rollback()
      finally:
          conn.close()
  ```

- [ ] **4.2** Sửa route `/parking/exit` để dùng hàm mới
  ```python
  success, result, error = process_payment_with_lock(
      vehicle_id, payment_method, card_id
  )
  ```

- [ ] **4.3** Test race condition
  ```bash
  python test_payment_security.py
  # Chạy test "Race Condition"
  ```

**Thời gian:** 1 giờ  
**Mức độ:** 🔴 CRITICAL

---

## 🟡 PHASE 2: SECURITY HARDENING (NÊN LÀM)

### ✅ Fix #5: Input Validation

**File cần sửa:** `app.py`

- [ ] **5.1** Tạo hàm `validate_payment_request()`
  ```python
  def validate_payment_request(data):
      errors = []
      # Validate vehicle_id
      # Validate payment_method
      # Validate card_id (nếu cần)
      return len(errors) == 0, errors
  ```

- [ ] **5.2** Thêm validation vào route
  ```python
  valid, errors = validate_payment_request(data)
  if not valid:
      return jsonify({'success': False, 'errors': errors}), 400
  ```

- [ ] **5.3** Test input validation
  ```bash
  python test_payment_security.py
  # Chạy test "Input Validation"
  ```

**Thời gian:** 30 phút  
**Mức độ:** 🟡 MEDIUM

---

### ✅ Fix #6: Rate Limiting

**File cần sửa:** `app.py`

- [ ] **6.1** Cài đặt Flask-Limiter
  ```bash
  pip install Flask-Limiter
  ```

- [ ] **6.2** Thêm rate limiting
  ```python
  from flask_limiter import Limiter
  
  limiter = Limiter(app, key_func=lambda: request.remote_addr)
  
  @app.route('/parking/exit', methods=['POST'])
  @limiter.limit("10 per minute")  # Giới hạn 10 requests/phút
  def parking_exit_page():
      # ...
  ```

**Thời gian:** 15 phút  
**Mức độ:** 🟡 MEDIUM

---

### ✅ Fix #7: Audit Logging

**File cần sửa:** `app.py`

- [ ] **7.1** Tạo bảng `payment_audit_log`
  ```sql
  CREATE TABLE payment_audit_log (
      id INT IDENTITY(1,1) PRIMARY KEY,
      vehicle_id INT,
      payment_method NVARCHAR(50),
      amount DECIMAL(10,2),
      status NVARCHAR(20),
      idempotency_key NVARCHAR(255),
      ip_address NVARCHAR(50),
      user_agent NVARCHAR(500),
      created_at DATETIME DEFAULT GETDATE()
  );
  ```

- [ ] **7.2** Log tất cả payment attempts
  ```python
  def log_payment_attempt(vehicle_id, payment_method, amount, status, idempotency_key):
      execute_db("""
          INSERT INTO payment_audit_log 
          (vehicle_id, payment_method, amount, status, idempotency_key, ip_address, user_agent)
          VALUES (?, ?, ?, ?, ?, ?, ?)
      """, [vehicle_id, payment_method, amount, status, idempotency_key, 
            request.remote_addr, request.user_agent.string])
  ```

**Thời gian:** 30 phút  
**Mức độ:** 🟡 MEDIUM

---

## 🧪 PHASE 3: TESTING (BẮT BUỘC)

### ✅ Test Suite

- [ ] **T1** Chạy tất cả security tests
  ```bash
  python test_payment_security.py
  ```

- [ ] **T2** Test thủ công: Double submit
  - Bấm nút "Xác nhận thanh toán" 10 lần liên tục
  - Kiểm tra: Chỉ 1 payment được xử lý

- [ ] **T3** Test thủ công: Price tampering
  - Mở DevTools (F12)
  - Sửa payload trong Network tab
  - Gửi request với `parking_fee: 1000`
  - Kiểm tra: Backend tính lại giá đúng

- [ ] **T4** Test thủ công: Race condition
  - Mở 2 browser tabs
  - Cùng thanh toán 1 xe
  - Kiểm tra: Chỉ 1 tab thành công

- [ ] **T5** Test thủ công: Network failure
  - Bấm thanh toán
  - Ngắt mạng giữa chừng
  - Kiểm tra: Rollback đúng, không mất tiền

- [ ] **T6** Test thủ công: Transaction rollback
  - Thanh toán bằng thẻ không tồn tại
  - Kiểm tra: Xe vẫn ở trạng thái 'parked'

**Thời gian:** 1 giờ  
**Mức độ:** 🔴 CRITICAL

---

## 📊 VERIFICATION CHECKLIST

### ✅ Code Review

- [ ] Tất cả database operations đều trong transaction
- [ ] Backend KHÔNG tin tưởng giá từ Frontend
- [ ] Tất cả requests đều có idempotency key
- [ ] Tất cả SELECT đều có row locking (nếu cần)
- [ ] Tất cả input đều được validate
- [ ] Tất cả errors đều được log
- [ ] Không có hardcoded credentials
- [ ] Không có SQL injection vulnerabilities

### ✅ Security Review

- [ ] Price tampering: KHÔNG thể sửa giá
- [ ] Double submit: KHÔNG thể gửi nhiều lần
- [ ] Race condition: KHÔNG thể thanh toán 2 lần
- [ ] Transaction rollback: Hoạt động đúng
- [ ] Input validation: Reject invalid input
- [ ] Rate limiting: Giới hạn requests/phút
- [ ] Audit logging: Log tất cả attempts

### ✅ Performance Review

- [ ] Response time < 500ms (bình thường)
- [ ] Response time < 2s (peak load)
- [ ] Database connection pooling
- [ ] Cache idempotency keys (Redis)
- [ ] Index trên các cột thường query

---

## 🚀 DEPLOYMENT CHECKLIST

### ✅ Pre-Deployment

- [ ] Tất cả tests đều PASS
- [ ] Code review hoàn tất
- [ ] Security review hoàn tất
- [ ] Backup database
- [ ] Chuẩn bị rollback plan

### ✅ Deployment

- [ ] Deploy code mới
- [ ] Chạy migration (nếu có)
- [ ] Restart Flask server
- [ ] Verify health check
- [ ] Monitor logs

### ✅ Post-Deployment

- [ ] Test payment flow trên Production
- [ ] Monitor error rate
- [ ] Monitor response time
- [ ] Check audit logs
- [ ] Verify no data loss

---

## 📝 ROLLBACK PLAN

Nếu có vấn đề sau khi deploy:

1. **Rollback code:**
   ```bash
   git revert HEAD
   git push
   ```

2. **Rollback database:**
   ```sql
   -- Restore từ backup
   ```

3. **Restart server:**
   ```bash
   sudo systemctl restart parking-app
   ```

4. **Verify:**
   - Test payment flow
   - Check logs
   - Monitor errors

---

## 🎯 SUCCESS CRITERIA

Hệ thống được coi là **PRODUCTION-READY** khi:

- ✅ Tất cả 4 fixes CRITICAL đã hoàn thành
- ✅ Tất cả security tests đều PASS
- ✅ Không có lỗ hổng bảo mật
- ✅ Response time < 500ms
- ✅ Error rate < 0.1%
- ✅ Audit logging hoạt động
- ✅ Rollback plan đã test

---

**Người lập:** Kiro AI - Senior QA Engineer  
**Ngày:** 12/04/2026  
**Version:** 1.0

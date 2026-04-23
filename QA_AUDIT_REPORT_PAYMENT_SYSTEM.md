# 🔴 BÁO CÁO KIỂM TOÁN BẢO MẬT & CHẤT LƯỢNG HỆ THỐNG THANH TOÁN

**Ngày kiểm toán:** 12/04/2026  
**Người thực hiện:** Senior QA Engineer & Security Auditor  
**Hệ thống:** Parking Management - Payment Flow  
**Mức độ nghiêm trọng:** 🔴 **CRITICAL** - Cần sửa ngay trước khi đưa vào Production

---

## 📋 TÓM TẮT ĐIỀU TRA

| Hạng mục | Trạng thái | Mức độ |
|----------|-----------|--------|
| **Data Integrity** | 🔴 FAIL | CRITICAL |
| **Transaction Safety** | 🔴 FAIL | CRITICAL |
| **Security (Price Tampering)** | 🔴 FAIL | CRITICAL |
| **Double Submit Prevention** | 🔴 FAIL | HIGH |
| **Error Recovery** | 🟡 PARTIAL | MEDIUM |
| **UI/UX Feedback** | 🟢 PASS | LOW |

**Kết luận:** Hệ thống hiện tại **KHÔNG AN TOÀN** để đưa vào Production. Phát hiện **4 lỗ hổng nghiêm trọng** có thể gây mất tiền hoặc dữ liệu sai lệch.

---

## 🔴 VẤN ĐỀ NGHIÊM TRỌNG #1: KHÔNG CÓ DATABASE TRANSACTION

### Mô tả vấn đề
Backend thực hiện **NHIỀU thao tác database riêng lẻ** mà không bọc trong transaction:

```python
# ❌ LỖI NGHIÊM TRỌNG: Không có transaction
if payment_method == 'card' and card_id:
    # Bước 1: Trừ tiền từ thẻ
    execute_db("UPDATE cards SET balance = balance - ? WHERE id=?", [parking_fee, card_id])
    # ⚠️ Nếu lỗi xảy ra ở đây → Tiền đã bị trừ!

# Bước 2: Cập nhật xe ra bãi
execute_db(
    "UPDATE vehicles SET status='exited', exit_time=?, actual_fee=?, payment_status='paid', payment_method=? WHERE id=?",
    [datetime.now(), parking_fee, payment_method, vehicle_id]
)
# ⚠️ Nếu lỗi xảy ra ở đây → Xe chưa ra nhưng tiền đã mất!
```

### Hậu quả
- ✅ Trừ tiền thành công từ thẻ thành viên
- ❌ Cập nhật xe ra bãi thất bại (lỗi database, mất kết nối...)
- 💸 **Khách hàng mất tiền nhưng xe vẫn báo "đang trong bãi"**
- 😡 Khiếu nại, mất uy tín, phải hoàn tiền thủ công

### Mức độ nghiêm trọng
🔴 **CRITICAL** - Có thể gây mất tiền thật

---

## 🔴 VẤN ĐỀ NGHIÊM TRỌNG #2: PRICE TAMPERING (Giá bị can thiệp)

### Mô tả vấn đề
Backend **TIN TƯỞNG 100%** giá tiền từ Frontend gửi lên:

```python
# ❌ LỖI BẢO MẬT NGHIÊM TRỌNG
parking_fee = data.get('parking_fee', 0)  # Lấy từ Frontend!

# Backend KHÔNG tính toán lại giá
# Chỉ lưu thẳng vào database
execute_db(
    "UPDATE vehicles SET actual_fee=?, ...",
    [parking_fee, ...]  # ← Giá từ Frontend, có thể bị hack!
)
```

### Kịch bản tấn công
1. Hacker mở DevTools (F12)
2. Sửa request payload:
   ```javascript
   // Giá thật: 50,000 đ
   // Hacker sửa thành:
   {
     "vehicle_id": 123,
     "parking_fee": 1000,  // ← Chỉ trả 1,000 đ!
     "payment_method": "cash"
   }
   ```
3. Backend nhận và lưu `actual_fee = 1000` vào database
4. 💸 **Khách hàng chỉ trả 1,000 đ cho phí đỗ 50,000 đ**

### Hậu quả
- Mất doanh thu nghiêm trọng
- Dữ liệu báo cáo sai lệch
- Có thể bị lợi dụng hàng loạt

### Mức độ nghiêm trọng
🔴 **CRITICAL** - Lỗ hổng bảo mật nghiêm trọng

---

## 🔴 VẤN ĐỀ NGHIÊM TRỌNG #3: DOUBLE SUBMIT (Spam Click)

### Mô tả vấn đề
Frontend **KHÔNG ngăn chặn** người dùng click nhiều lần:

```javascript
// ❌ KHÔNG ĐỦ: Chỉ disable button
btn.disabled = true;

// ⚠️ Nhưng nếu user click nhanh 3 lần trước khi disable?
// → 3 request được gửi đồng thời!
```

### Kịch bản xảy ra
1. Nhân viên bấm "Xác nhận thanh toán"
2. Mạng chậm → Chưa thấy phản hồi
3. Nhân viên bấm thêm 2 lần nữa (hoảng loạn)
4. Backend nhận **3 request giống hệt nhau**
5. Kết quả:
   - Trừ tiền thẻ **3 lần** (nếu thanh toán bằng thẻ)
   - Hoặc ghi log sai 3 lần
   - Database bị cập nhật nhiều lần

### Hậu quả
- Trừ tiền sai
- Dữ liệu bị duplicate
- Khách hàng khiếu nại

### Mức độ nghiêm trọng
🔴 **CRITICAL** - Có thể gây mất tiền

---

## 🔴 VẤN ĐỀ NGHIÊM TRỌNG #4: RACE CONDITION (Xe đã ra nhưng vẫn thanh toán được)

### Mô tả vấn đề
Backend kiểm tra trạng thái xe **TRƯỚC KHI** thanh toán, nhưng không lock record:

```python
# Bước 1: Kiểm tra xe
vehicle = query_db("SELECT * FROM vehicles WHERE id=? AND status='parked'", [vehicle_id], one=True)
# ⚠️ Tại thời điểm này, xe vẫn đang "parked"

# ... 5 giây sau (mạng chậm) ...

# Bước 2: Cập nhật xe ra bãi
execute_db("UPDATE vehicles SET status='exited' ...")
# ⚠️ Nhưng có thể xe đã được cập nhật bởi request khác!
```

### Kịch bản xảy ra
1. **Request A:** Nhân viên 1 bấm thanh toán xe #123
2. **Request B:** Nhân viên 2 cũng bấm thanh toán xe #123 (cùng lúc)
3. Cả 2 request đều pass qua kiểm tra `status='parked'`
4. Cả 2 request đều trừ tiền và cập nhật database
5. 💸 **Xe #123 bị tính phí 2 lần!**

### Hậu quả
- Thu tiền 2 lần cho 1 xe
- Dữ liệu sai lệch
- Khách hàng khiếu nại

### Mức độ nghiêm trọng
🔴 **CRITICAL** - Có thể gây mất tiền

---

## 🟡 VẤN ĐỀ TRUNG BÌNH #5: KHÔNG CÓ ROLLBACK KHI LỖI

### Mô tả vấn đề
Hàm `execute_db()` **LUÔN COMMIT** dù có lỗi hay không:

```python
def execute_db(query, args=()):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(query, args)
    # ... lấy ID ...
    conn.commit()  # ← LUÔN COMMIT!
    conn.close()
    return last_id
```

### Hậu quả
- Nếu có lỗi ở giữa transaction → Dữ liệu bị lệch pha
- Không thể rollback

### Mức độ nghiêm trọng
🟡 **MEDIUM** - Cần cải thiện

---

## 🟡 VẤN ĐỀ TRUNG BÌNH #6: KHÔNG VALIDATE INPUT

### Mô tả vấn đề
Backend không validate đầy đủ:

```python
# ❌ Không kiểm tra parking_fee > 0
parking_fee = data.get('parking_fee', 0)

# ❌ Không kiểm tra payment_method hợp lệ
payment_method = data.get('payment_method', 'cash')

# ❌ Không kiểm tra vehicle_id là số
vehicle_id = data.get('vehicle_id')
```

### Hậu quả
- Có thể lưu `parking_fee = -1000` (số âm)
- Có thể lưu `payment_method = "hacked"`
- Có thể gây lỗi SQL injection

### Mức độ nghiêm trọng
🟡 **MEDIUM** - Cần validate

---

## 🟢 ĐIỂM MẠNH

1. ✅ Frontend có loading spinner
2. ✅ Frontend kiểm tra Content-Type
3. ✅ Backend có try-except bao bọc
4. ✅ Backend có logging
5. ✅ UI/UX thân thiện

---

## 🔧 GIẢI PHÁP TOÀN DIỆN

### 1. Thêm Database Transaction (CRITICAL)

```python
def execute_transaction(operations):
    """
    Thực thi nhiều operations trong 1 transaction
    operations: list of (query, args)
    """
    conn = get_db()
    cursor = conn.cursor()
    try:
        for query, args in operations:
            cursor.execute(query, args)
        conn.commit()
        return True, None
    except Exception as e:
        conn.rollback()
        app.logger.error(f"❌ Transaction failed: {str(e)}")
        return False, str(e)
    finally:
        conn.close()
```

### 2. Tính toán lại giá ở Backend (CRITICAL)

```python
# ✅ ĐÚNG: Backend tự tính giá, không tin Frontend
def calculate_parking_fee(vehicle_id):
    """Tính phí đỗ xe dựa trên thời gian thực tế"""
    vehicle = query_db("SELECT * FROM vehicles WHERE id=? AND status='parked'", [vehicle_id], one=True)
    if not vehicle:
        return None, "Không tìm thấy xe"
    
    entry = vehicle.get('entry_time')
    if isinstance(entry, str):
        entry = datetime.fromisoformat(entry)
    
    diff = datetime.now() - entry
    hours = max(1, int(diff.total_seconds() / 3600) + (1 if diff.total_seconds() % 3600 > 0 else 0))
    
    # Lấy giá từ bảng pricing (không tin Frontend)
    rate = 15000 if vehicle.get('vehicle_type') == 'Xe hơi' else 5000
    fee = hours * rate
    
    return fee, None
```

### 3. Thêm Idempotency Key (CRITICAL)

```python
# Frontend tạo unique key cho mỗi request
const idempotencyKey = `${vehicle_id}-${Date.now()}-${Math.random()}`;

fetch('/parking/exit', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-Idempotency-Key': idempotencyKey
    },
    body: JSON.stringify({...})
});

# Backend kiểm tra key đã xử lý chưa
processed_keys = {}  # Hoặc dùng Redis

@app.route('/parking/exit', methods=['POST'])
def parking_exit_page():
    idempotency_key = request.headers.get('X-Idempotency-Key')
    
    if idempotency_key in processed_keys:
        # Đã xử lý rồi, trả về kết quả cũ
        return jsonify(processed_keys[idempotency_key])
    
    # Xử lý bình thường...
    result = process_payment(...)
    
    # Lưu kết quả
    processed_keys[idempotency_key] = result
    return jsonify(result)
```

### 4. Thêm Row Locking (CRITICAL)

```python
# ✅ ĐÚNG: Lock row khi đang xử lý
def process_payment_with_lock(vehicle_id, payment_method):
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Lock row để tránh race condition
        cursor.execute("""
            SELECT * FROM vehicles WITH (UPDLOCK, ROWLOCK)
            WHERE id=? AND status='parked'
        """, [vehicle_id])
        
        vehicle = cursor.fetchone()
        if not vehicle:
            conn.rollback()
            return False, "Xe không tồn tại hoặc đã ra bãi"
        
        # Tính phí
        fee = calculate_fee(vehicle)
        
        # Trừ tiền thẻ (nếu có)
        if payment_method == 'card':
            cursor.execute("UPDATE cards SET balance = balance - ? WHERE id=?", [fee, card_id])
        
        # Cập nhật xe
        cursor.execute("""
            UPDATE vehicles 
            SET status='exited', exit_time=?, actual_fee=?, payment_method=?
            WHERE id=?
        """, [datetime.now(), fee, payment_method, vehicle_id])
        
        conn.commit()
        return True, fee
        
    except Exception as e:
        conn.rollback()
        app.logger.error(f"❌ Payment failed: {str(e)}")
        return False, str(e)
    finally:
        conn.close()
```

### 5. Validate Input (MEDIUM)

```python
def validate_payment_request(data):
    """Validate input từ Frontend"""
    errors = []
    
    vehicle_id = data.get('vehicle_id')
    if not vehicle_id or not isinstance(vehicle_id, int):
        errors.append("vehicle_id không hợp lệ")
    
    payment_method = data.get('payment_method')
    valid_methods = ['cash', 'member_card', 'momo', 'vnpay', 'stripe']
    if payment_method not in valid_methods:
        errors.append(f"payment_method phải là một trong: {valid_methods}")
    
    # KHÔNG validate parking_fee từ Frontend (sẽ tính lại ở Backend)
    
    return len(errors) == 0, errors
```

### 6. Frontend: Ngăn Double Submit (HIGH)

```javascript
let isProcessing = false;  // Flag toàn cục

async function processPayment() {
    // ✅ Kiểm tra flag trước
    if (isProcessing) {
        console.warn('⚠️ Đang xử lý, vui lòng đợi...');
        return;
    }
    
    isProcessing = true;  // Set flag
    
    const btn = document.getElementById('btnPay');
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Đang xử lý...';
    
    try {
        // Tạo idempotency key
        const idempotencyKey = `${currentVehicle.id}-${Date.now()}-${Math.random()}`;
        
        const res = await fetch('/parking/exit', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Idempotency-Key': idempotencyKey
            },
            body: JSON.stringify({
                vehicle_id: currentVehicle.id,
                payment_method: selectedPayment,
                // ❌ KHÔNG gửi parking_fee từ Frontend
                card_id: selectedPayment === 'card' ? document.getElementById('payCardId').value : null
            })
        });
        
        // ... xử lý response ...
        
    } finally {
        isProcessing = false;  // Reset flag
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-check-circle"></i> Xác nhận thanh toán';
    }
}
```

---

## 📊 BẢNG SO SÁNH TRƯỚC/SAU

| Vấn đề | Trước | Sau |
|--------|-------|-----|
| **Transaction** | ❌ Không có | ✅ Có rollback |
| **Price Tampering** | ❌ Tin Frontend | ✅ Backend tính lại |
| **Double Submit** | ❌ Không ngăn | ✅ Idempotency key |
| **Race Condition** | ❌ Không lock | ✅ Row locking |
| **Input Validation** | ❌ Không validate | ✅ Validate đầy đủ |
| **Error Recovery** | 🟡 Partial | ✅ Full rollback |

---

## 🎯 CHECKLIST TRIỂN KHAI

### Phase 1: Critical Fixes (BẮT BUỘC)
- [ ] Thêm database transaction với rollback
- [ ] Backend tính lại giá, không tin Frontend
- [ ] Thêm row locking để tránh race condition
- [ ] Thêm idempotency key để ngăn double submit

### Phase 2: Security Hardening
- [ ] Validate tất cả input từ Frontend
- [ ] Thêm rate limiting (giới hạn số request/phút)
- [ ] Log tất cả transaction để audit
- [ ] Thêm alert khi phát hiện hành vi bất thường

### Phase 3: Testing
- [ ] Test double submit (click nhanh 10 lần)
- [ ] Test race condition (2 user cùng thanh toán 1 xe)
- [ ] Test price tampering (sửa giá trong DevTools)
- [ ] Test network failure (ngắt mạng giữa chừng)
- [ ] Test rollback (gây lỗi cố ý để test rollback)

---

## 🚨 KHUYẾN NGHỊ

**KHÔNG ĐƯA VÀO PRODUCTION** cho đến khi sửa xong 4 vấn đề CRITICAL:
1. ✅ Database Transaction
2. ✅ Price Recalculation
3. ✅ Idempotency Key
4. ✅ Row Locking

**Thời gian ước tính:** 4-6 giờ để implement tất cả fixes

**Mức độ ưu tiên:** 🔴 **URGENT** - Liên quan trực tiếp đến tiền bạc

---

**Người lập báo cáo:** Kiro AI - Senior QA Engineer  
**Ngày:** 12/04/2026  
**Trạng thái:** 🔴 CRITICAL - Cần sửa ngay

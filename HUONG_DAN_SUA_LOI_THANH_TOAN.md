# 🔧 HƯỚNG DẪN SỬA LỖI THANH TOÁN XE RA BÃI

## 📋 MÔ TẢ VẤN ĐỀ

**Lỗi gặp phải:**
```
[SQL Server]Invalid column name 'payment_method'
```

**Nguyên nhân:**
- Database thiếu cột `payment_method` trong bảng `vehicles`
- Backend đã cố gắng lưu giá trị vào cột không tồn tại
- Lỗi SQL được hiển thị trực tiếp ra giao diện người dùng (không chuyên nghiệp)

---

## ✅ GIẢI PHÁP ĐÃ THỰC HIỆN

### 1️⃣ **CẬP NHẬT DATABASE**

**File:** `add_payment_method_column.sql`

**Các thay đổi:**
- ✅ Thêm cột `payment_method NVARCHAR(50)` vào bảng `vehicles`
- ✅ Thêm constraint kiểm tra giá trị hợp lệ: `cash`, `member_card`, `momo`, `vnpay`, `stripe`
- ✅ Tạo index `IX_vehicles_payment_method` để tăng tốc truy vấn
- ✅ Cập nhật giá trị mặc định `'cash'` cho các xe đã thanh toán trước đó

**Cách chạy script:**
```sql
-- Mở SQL Server Management Studio (SSMS)
-- Kết nối đến: LAPTOP-3J6T1I18\SQLEXPRESS01
-- Chọn database: ParkingManagement
-- Mở file: add_payment_method_column.sql
-- Nhấn F5 để chạy
```

**Kết quả mong đợi:**
```
✅ Đã thêm cột payment_method vào bảng vehicles
✅ Đã thêm constraint CK_vehicles_payment_method
✅ Đã tạo index IX_vehicles_payment_method
✅ Đã cập nhật X xe đã thanh toán trước đó với payment_method = 'cash'
```

---

### 2️⃣ **NÂNG CẤP BACKEND API**

**File:** `app.py` - Route `/parking/exit`

**Các cải tiến:**

#### ✅ Bọc logic database trong try-except
```python
try:
    execute_db(
        "UPDATE vehicles SET status='exited', exit_time=?, actual_fee=?, payment_status='paid', payment_method=? WHERE id=?",
        [datetime.now(), parking_fee, payment_method, vehicle_id]
    )
    app.logger.info(f"✅ Xe #{vehicle_id} đã ra bãi - Phí: {parking_fee} - Phương thức: {payment_method}")
    return jsonify({
        'success': True,
        'message': 'Xe đã ra bãi thành công',
        'parking_fee': parking_fee,
        'payment_method': payment_method,
        'pay_url': None,
    })
except Exception as e:
    app.logger.error(f"❌ Lỗi cập nhật xe #{vehicle_id} ra bãi: {str(e)}")
    return jsonify({
        'success': False, 
        'message': 'Lỗi hệ thống: Không thể ghi nhận thanh toán. Vui lòng liên hệ kỹ thuật.',
        'error_detail': str(e) if app.debug else None
    })
```

#### ✅ Thêm logging chi tiết
- Log thành công: `✅ Xe #123 đã ra bãi - Phí: 15000 - Phương thức: cash`
- Log lỗi: `❌ Lỗi cập nhật xe #123 ra bãi: Invalid column name 'payment_method'`

#### ✅ Trả về JSON thay vì HTML error
- **Trước:** Backend văng lỗi SQL → Trả về HTML error page → Frontend parse JSON thất bại
- **Sau:** Backend bắt lỗi → Trả về JSON với `success: false` → Frontend hiển thị thông báo đẹp

#### ✅ Thêm trường `payment_method` vào response
```json
{
  "success": true,
  "message": "Xe đã ra bãi thành công",
  "parking_fee": 15000,
  "payment_method": "cash",
  "pay_url": null
}
```

---

### 3️⃣ **CẢI THIỆN FRONTEND UI/UX**

**File:** `parking/exit.html` - Hàm `processPayment()`

**Các cải tiến:**

#### ✅ Kiểm tra Content-Type trước khi parse JSON
```javascript
const contentType = res.headers.get('content-type');
if (!contentType || !contentType.includes('application/json')) {
    const text = await res.text();
    console.error('❌ Backend trả về HTML thay vì JSON:', text);
    throw new Error('Lỗi hệ thống: Server trả về định dạng không hợp lệ');
}
```

#### ✅ Loading spinner chuyên nghiệp
```javascript
btn.disabled = true;
btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Đang xử lý thanh toán...';
```

#### ✅ Hiển thị thông báo lỗi thân thiện
- **Trước:** `Unexpected token '<', "<!DOCTYPE "... is not valid JSON`
- **Sau:** `Lỗi hệ thống: Không thể ghi nhận thanh toán. Vui lòng liên hệ kỹ thuật.`

#### ✅ Toast notification với icon
```javascript
showPayAlert('<i class="fas fa-check-circle"></i> Thanh toán thành công!', 'success');
showPayAlert('<i class="fas fa-exclamation-circle"></i> ' + errorMsg, 'danger');
```

#### ✅ Tự động chuyển sang màn hình kết quả
```javascript
setTimeout(() => {
    showExitSuccess(payload.parking_fee, selectedPayment);
}, 800);
```

#### ✅ Hỗ trợ thêm phương thức thanh toán
```javascript
const methodNames = { 
    cash: 'Tiền mặt', 
    card: 'Thẻ thành viên', 
    member_card: 'Thẻ thành viên',
    momo: 'MoMo', 
    vnpay: 'VNPay',
    stripe: 'Stripe'
};
```

#### ✅ Xử lý popup bị chặn
```javascript
const payWin = window.open(data.pay_url, '_blank', 'width=500,height=700');
if (!payWin) {
    showPayAlert('<i class="fas fa-exclamation-triangle"></i> Vui lòng cho phép popup để mở trang thanh toán!', 'warning');
}
```

---

## 🚀 CÁCH SỬ DỤNG

### Bước 1: Chạy SQL Script
```bash
# Mở SQL Server Management Studio
# File → Open → File → Chọn add_payment_method_column.sql
# Nhấn F5 để chạy
```

### Bước 2: Khởi động lại Flask Server
```bash
# Dừng server hiện tại (Ctrl+C)
python app.py
```

### Bước 3: Test chức năng
1. Vào trang **Xe Ra Bãi**: `http://localhost:5000/parking/exit`
2. Tìm một xe đang đỗ (quét QR hoặc nhập biển số)
3. Chọn phương thức thanh toán (Tiền mặt, Thẻ thành viên, MoMo, VNPay)
4. Nhấn **"Xác nhận thanh toán"**
5. Kiểm tra:
   - ✅ Không còn lỗi SQL
   - ✅ Hiển thị loading spinner
   - ✅ Thông báo thành công/lỗi đẹp mắt
   - ✅ Tự động chuyển sang màn hình kết quả

---

## 📊 PHƯƠNG THỨC THANH TOÁN HỖ TRỢ

| Mã | Tên hiển thị | Mô tả |
|---|---|---|
| `cash` | Tiền mặt | Thanh toán trực tiếp bằng tiền mặt |
| `member_card` | Thẻ thành viên | Trừ tiền từ thẻ thành viên |
| `card` | Thẻ thành viên | Alias của `member_card` |
| `momo` | MoMo | Thanh toán qua ví điện tử MoMo |
| `vnpay` | VNPay | Thanh toán qua cổng VNPay |
| `stripe` | Stripe | Thanh toán qua Stripe (thẻ quốc tế) |

---

## 🔍 KIỂM TRA DATABASE

### Xem cột vừa tạo
```sql
SELECT 
    COLUMN_NAME AS 'Tên cột',
    DATA_TYPE AS 'Kiểu dữ liệu',
    CHARACTER_MAXIMUM_LENGTH AS 'Độ dài',
    IS_NULLABLE AS 'Cho phép NULL'
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'vehicles' 
  AND COLUMN_NAME = 'payment_method';
```

### Xem các xe đã thanh toán
```sql
SELECT TOP 10
    id,
    license_plate AS 'Biển số',
    vehicle_type AS 'Loại xe',
    actual_fee AS 'Phí đỗ',
    payment_method AS 'Phương thức',
    exit_time AS 'Giờ ra'
FROM vehicles
WHERE status = 'exited'
  AND payment_method IS NOT NULL
ORDER BY exit_time DESC;
```

### Thống kê theo phương thức thanh toán
```sql
SELECT 
    payment_method AS 'Phương thức',
    COUNT(*) AS 'Số lượng',
    SUM(actual_fee) AS 'Tổng tiền'
FROM vehicles
WHERE status = 'exited'
  AND payment_method IS NOT NULL
GROUP BY payment_method
ORDER BY COUNT(*) DESC;
```

---

## 🐛 XỬ LÝ LỖI

### Lỗi: "Invalid column name 'payment_method'"
**Nguyên nhân:** Chưa chạy SQL script  
**Giải pháp:** Chạy file `add_payment_method_column.sql`

### Lỗi: "Unexpected token '<'"
**Nguyên nhân:** Backend trả về HTML thay vì JSON  
**Giải pháp:** Đã fix trong code mới, kiểm tra Content-Type trước khi parse

### Lỗi: "Không thể ghi nhận thanh toán"
**Nguyên nhân:** Lỗi database hoặc kết nối  
**Giải pháp:** 
1. Kiểm tra log trong terminal Flask
2. Kiểm tra kết nối SQL Server
3. Xem chi tiết lỗi trong `error_detail` (nếu `app.debug = True`)

---

## 📝 CHANGELOG

### Version 1.0 (12/04/2026)
- ✅ Thêm cột `payment_method` vào bảng `vehicles`
- ✅ Thêm constraint và index cho `payment_method`
- ✅ Bọc logic database trong try-except
- ✅ Thêm logging chi tiết
- ✅ Cải thiện error handling ở Frontend
- ✅ Thêm loading spinner và toast notification
- ✅ Hỗ trợ 6 phương thức thanh toán

---

## 👨‍💻 LIÊN HỆ HỖ TRỢ

Nếu gặp vấn đề, vui lòng:
1. Kiểm tra log trong terminal Flask
2. Kiểm tra Console trong trình duyệt (F12)
3. Chạy lại SQL script `add_payment_method_column.sql`
4. Khởi động lại Flask server

---

**Tác giả:** Kiro AI Assistant  
**Ngày tạo:** 12/04/2026  
**Phiên bản:** 1.0

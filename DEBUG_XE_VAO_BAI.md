# 🔧 HƯỚNG DẪN DEBUG LỖI "XE VÀO BÃI"

## ❌ Lỗi gặp phải
```
Lỗi kết nối: Unexpected token '<'
```

## ✅ Đã sửa

### 1. **Backend (app.py)**
- ✅ Thêm try-catch toàn diện cho mọi bước xử lý
- ✅ Đảm bảo **LUÔN** trả về JSON (không bao giờ trả về HTML)
- ✅ Thêm error_code để phân loại lỗi
- ✅ Log chi tiết lỗi vào console
- ✅ Đơn giản hóa INSERT query (chỉ các cột cơ bản)

### 2. **Frontend (parking/entry.html)**
- ✅ Kiểm tra Content-Type trước khi parse JSON
- ✅ Xử lý trường hợp server trả về HTML
- ✅ Hiển thị thông báo lỗi thân thiện
- ✅ Log chi tiết vào console để debug
- ✅ Phân loại lỗi theo error_code

---

## 🧪 Cách test

### **Bước 1: Restart Flask Server**
```bash
# Stop server cũ (Ctrl+C)
python app.py
```

### **Bước 2: Mở Browser Console**
- Nhấn F12 → Tab Console
- Để xem log chi tiết nếu có lỗi

### **Bước 3: Test chức năng**
1. Truy cập: `http://localhost:5000/parking`
2. Nhập biển số: `99-E1 222.68`
3. Chọn loại xe: Xe máy
4. Bấm "Xác nhận xe vào bãi"

### **Bước 4: Kiểm tra kết quả**

#### ✅ **Nếu thành công:**
- Hiển thị thông báo: "Xe đã vào bãi thành công"
- Chuyển sang màn hình kết quả
- Console không có lỗi

#### ❌ **Nếu thất bại:**
- Kiểm tra Console (F12) → Tab Console
- Tìm dòng bắt đầu bằng `❌`
- Copy toàn bộ log và gửi cho developer

---

## 🔍 Các loại lỗi có thể gặp

### **1. Lỗi Database**
```
Error Code: DB_INSERT_ERROR
Message: Lỗi lưu thông tin xe vào hệ thống
```

**Nguyên nhân:**
- Thiếu cột trong bảng `vehicles`
- Lỗi kết nối SQL Server
- Dữ liệu không hợp lệ

**Cách sửa:**
```sql
-- Kiểm tra cấu trúc bảng
SELECT COLUMN_NAME, DATA_TYPE 
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'vehicles';

-- Kiểm tra kết nối
SELECT @@VERSION;
```

### **2. Lỗi Biển số đã tồn tại**
```
Error Code: ALREADY_PARKED
Message: Xe 99-E1 222.68 đang trong bãi!
```

**Cách sửa:**
```sql
-- Xem xe đang trong bãi
SELECT * FROM vehicles WHERE status='parked';

-- Xóa xe test (nếu cần)
DELETE FROM vehicles WHERE license_plate='99-E1 222.68';
```

### **3. Lỗi Bãi đầy**
```
Error Code: PARKING_FULL
Message: Khu Xe máy đã đầy! (100/100)
```

**Cách sửa:**
```sql
-- Tăng sức chứa
UPDATE parking_config 
SET motorbike_capacity = 200 
WHERE id = 1;
```

### **4. Lỗi Không nhận được dữ liệu**
```
Error Code: NO_DATA
Message: Không nhận được dữ liệu từ client
```

**Nguyên nhân:**
- Frontend không gửi JSON đúng format
- Header Content-Type sai

**Cách sửa:**
- Kiểm tra Network tab trong F12
- Xem Request Payload có đúng không

---

## 📊 Kiểm tra Log Server

### **Xem log Flask:**
```bash
# Log sẽ hiển thị trong terminal đang chạy Flask
# Tìm các dòng:
# - "Lỗi INSERT database: ..."
# - "⚠️  CẢNH BÁO: Xe nghi ngờ - ..."
# - "Lỗi lưu snapshot: ..."
```

### **Xem log SQL Server:**
```sql
-- Kiểm tra xe vừa thêm
SELECT TOP 10 * 
FROM vehicles 
ORDER BY entry_time DESC;

-- Kiểm tra số lượng xe trong bãi
SELECT 
    vehicle_type,
    COUNT(*) as total,
    SUM(CASE WHEN status='parked' THEN 1 ELSE 0 END) as parked
FROM vehicles
GROUP BY vehicle_type;
```

---

## 🛠️ Công cụ Debug

### **1. Test API bằng curl:**
```bash
curl -X POST http://localhost:5000/parking \
  -H "Content-Type: application/json" \
  -d '{
    "license_plate": "99-E1 222.68",
    "vehicle_type": "Xe máy",
    "plate_color": "Trắng",
    "plate_type": "Biển thường",
    "card_id": null,
    "is_manual_entry": false,
    "is_suspicious": false,
    "entry_method": "ocr"
  }'
```

### **2. Test API bằng Postman:**
- Method: POST
- URL: `http://localhost:5000/parking`
- Headers: `Content-Type: application/json`
- Body (raw JSON):
```json
{
  "license_plate": "99-E1 222.68",
  "vehicle_type": "Xe máy",
  "plate_color": "Trắng",
  "plate_type": "Biển thường"
}
```

---

## 📝 Checklist Debug

- [ ] Flask server đang chạy
- [ ] SQL Server đang chạy
- [ ] Database `ParkingManagement` tồn tại
- [ ] Bảng `vehicles` có đủ cột
- [ ] Bảng `parking_config` có dữ liệu
- [ ] Browser console không có lỗi JavaScript
- [ ] Network tab hiển thị request thành công (200)
- [ ] Response là JSON (không phải HTML)

---

## 🆘 Nếu vẫn lỗi

### **Thu thập thông tin:**
1. Screenshot màn hình lỗi
2. Copy toàn bộ Console log (F12)
3. Copy toàn bộ Network request/response (F12 → Network)
4. Copy log từ Flask terminal
5. Chạy query kiểm tra database:

```sql
-- Kiểm tra cấu trúc bảng
EXEC sp_help 'vehicles';

-- Kiểm tra dữ liệu
SELECT TOP 5 * FROM vehicles ORDER BY id DESC;
SELECT * FROM parking_config;
```

### **Gửi thông tin cho developer:**
- Screenshot
- Console log
- Network log
- Flask terminal log
- SQL query results

---

**Tài liệu này được tạo để debug lỗi "Unexpected token '<'"**

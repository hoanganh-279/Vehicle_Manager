# 🛡️ HƯỚNG DẪN SỬ DỤNG FALLBACK WORKFLOW - HỆ THỐNG XE VÀO BÃI

## 📋 Tổng quan

Hệ thống Fallback Workflow được thiết kế để xử lý các trường hợp OCR (nhận diện biển số tự động) thất bại do:
- Biển số dính bùn đất
- Ánh sáng chói quá mức
- Biển số giả (decal dán đè)
- Camera góc chụp không tốt
- Thời tiết xấu (mưa, sương mù)

---

## 🎯 Các tính năng chính

### 1. **Chế độ Nhập Thủ Công (Manual Override Mode)**
- Tự động kích hoạt khi OCR thất bại hoặc timeout (>3 giây)
- Bảo vệ có thể bấm nút "Nhập tay" để nhập biển số thủ công
- Ô input biển số sẽ được mở khóa và đổi màu cảnh báo (màu cam)

### 2. **Bắt buộc Lưu Bằng Chứng (Audit Trail)**
- Hệ thống **BẮT BUỘC** chụp ảnh trước khi cho phép nhập tay
- Ảnh snapshot được lưu vào database kèm timestamp
- Metadata đầy đủ được ghi lại để tra soát

### 3. **Đánh dấu Xe Nghi ngờ (Suspicious Flag)**
- Checkbox "Đánh dấu xe đáng nghi ngờ" xuất hiện khi nhập tay
- Khi tick, hệ thống lưu cảnh báo đỏ vào database
- Nhân viên cổng ra sẽ nhận được cảnh báo kiểm tra kỹ giấy tờ

### 4. **Đối chiếu Chéo (Cross-check View)**
- Hiển thị ảnh chụp thực tế bên cạnh biển số nhập vào
- Ép buộc bảo vệ phải đối chiếu trước khi xác nhận
- Giảm thiểu sai sót và gian lận

---

## 🔄 Quy trình sử dụng

### **Trường hợp 1: OCR thành công (Bình thường)**
```
1. Bảo vệ bấm "Chụp biển số"
2. Hệ thống nhận diện tự động → Hiển thị kết quả
3. Bảo vệ kiểm tra → Bấm "Xác nhận"
4. Xe vào bãi thành công
```

### **Trường hợp 2: OCR thất bại (Fallback)**
```
1. Bảo vệ bấm "Chụp biển số"
2. Hệ thống không nhận diện được (timeout hoặc lỗi)
3. Nút "Nhập tay" sáng lên và nhấp nháy
4. Bảo vệ bấm "Nhập tay"
5. Ô input biển số mở khóa (màu cam)
6. Bảo vệ nhập biển số thủ công
7. Nếu nghi ngờ biển giả → Tick checkbox "Đánh dấu xe đáng nghi ngờ"
8. Hệ thống hiển thị "Comparison View" để đối chiếu
9. Bảo vệ kiểm tra ảnh vs biển số → Bấm "Xác nhận xe vào bãi"
10. Xe vào bãi + Lưu audit trail
```

---

## 📊 Cấu trúc dữ liệu gửi lên Backend

### **JSON Payload - Trường hợp OCR thành công**
```json
{
  "license_plate": "99-E1 222.68",
  "vehicle_type": "Xe máy",
  "plate_color": "Trắng",
  "plate_type": "Biển thường",
  "card_id": null,
  
  "is_manual_entry": false,
  "is_suspicious": false,
  "snapshot_image": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
  "capture_timestamp": "2025-04-11T14:30:45.123Z",
  "entry_method": "ocr",
  
  "audit_metadata": {
    "ocr_failed": false,
    "manual_override_reason": null,
    "suspicious_flag": false,
    "operator_notes": "Nhận diện tự động",
    "timestamp": "2025-04-11T14:30:45.123Z"
  }
}
```

### **JSON Payload - Trường hợp Fallback (Nhập tay + Nghi ngờ)**
```json
{
  "license_plate": "51A-123.45",
  "vehicle_type": "Xe hơi",
  "plate_color": "Trắng",
  "plate_type": "Biển thường",
  "card_id": "CARD001",
  
  "is_manual_entry": true,
  "is_suspicious": true,
  "snapshot_image": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
  "capture_timestamp": "2025-04-11T14:35:20.456Z",
  "entry_method": "manual",
  
  "audit_metadata": {
    "ocr_failed": true,
    "manual_override_reason": "OCR failed or timeout",
    "suspicious_flag": true,
    "operator_notes": "Nhập tay do OCR thất bại",
    "timestamp": "2025-04-11T14:35:20.456Z"
  }
}
```

---

## 🗄️ Cấu trúc Database

### **Bảng `vehicles` - Các cột mới**

| Cột | Kiểu dữ liệu | Mô tả |
|-----|-------------|-------|
| `is_manual_entry` | BIT | Đánh dấu xe nhập tay (0=OCR, 1=Manual) |
| `is_suspicious` | BIT | Đánh dấu xe nghi ngờ (0=Bình thường, 1=Nghi ngờ) |
| `entry_method` | NVARCHAR(20) | Phương thức nhập: 'ocr' hoặc 'manual' |
| `snapshot_image_path` | NVARCHAR(500) | Đường dẫn ảnh chụp snapshot |
| `capture_timestamp` | DATETIME | Thời điểm chụp ảnh |
| `manual_override_reason` | NVARCHAR(500) | Lý do nhập tay |
| `audit_metadata` | NVARCHAR(MAX) | JSON metadata đầy đủ |

### **View `vw_suspicious_vehicles`**
View này tự động lọc và hiển thị các xe nghi ngờ:
```sql
SELECT * FROM vw_suspicious_vehicles
WHERE entry_time >= '2025-04-01'
ORDER BY entry_time DESC;
```

### **Stored Procedure `sp_get_audit_trail_report`**
Lấy báo cáo audit trail theo khoảng thời gian:
```sql
EXEC sp_get_audit_trail_report 
    @start_date = '2025-04-01', 
    @end_date = '2025-04-30',
    @suspicious_only = 1;  -- Chỉ lấy xe nghi ngờ
```

---

## 🔍 Tra soát và Kiểm tra

### **1. Xem danh sách xe nhập tay**
```sql
SELECT 
    license_plate,
    entry_time,
    snapshot_image_path,
    manual_override_reason,
    audit_metadata
FROM vehicles
WHERE is_manual_entry = 1
ORDER BY entry_time DESC;
```

### **2. Xem danh sách xe nghi ngờ**
```sql
SELECT 
    license_plate,
    entry_time,
    exit_time,
    status,
    snapshot_image_path,
    is_manual_entry,
    audit_metadata
FROM vehicles
WHERE is_suspicious = 1
ORDER BY entry_time DESC;
```

### **3. Xem xe nghi ngờ cao (Nhập tay + Đánh dấu nghi ngờ)**
```sql
SELECT 
    license_plate,
    entry_time,
    snapshot_image_path,
    manual_override_reason,
    audit_metadata
FROM vehicles
WHERE is_manual_entry = 1 
  AND is_suspicious = 1
ORDER BY entry_time DESC;
```

---

## ⚠️ Lưu ý quan trọng

### **Cho Bảo vệ:**
1. **LUÔN** chụp ảnh trước khi nhập tay (hệ thống bắt buộc)
2. Kiểm tra kỹ ảnh chụp và biển số nhập vào trong "Comparison View"
3. Chỉ tick "Đánh dấu xe đáng nghi ngờ" khi thực sự nghi ngờ biển giả
4. Ghi chú rõ ràng nếu có vấn đề bất thường

### **Cho Quản lý:**
1. Định kỳ kiểm tra báo cáo audit trail (hàng ngày/tuần)
2. Rà soát các xe nhập tay để phát hiện gian lận
3. Kiểm tra ảnh snapshot của các xe nghi ngờ
4. Đào tạo nhân viên về quy trình fallback

### **Cho Developer:**
1. Ảnh snapshot được lưu tại: `static/uploads/snapshots/`
2. Định kỳ backup thư mục này
3. Cân nhắc nén ảnh để tiết kiệm dung lượng
4. Monitor dung lượng database (cột `audit_metadata` có thể lớn)

---

## 🚀 Cài đặt

### **Bước 1: Cập nhật Database**
```bash
# Chạy script SQL
sqlcmd -S LAPTOP-3J6T1I18\SQLEXPRESS01 -d ParkingManagement -i update_vehicles_table_fallback.sql
```

### **Bước 2: Tạo thư mục lưu ảnh**
```bash
mkdir -p static/uploads/snapshots
```

### **Bước 3: Restart Flask Server**
```bash
python app.py
```

### **Bước 4: Test chức năng**
1. Truy cập: `http://localhost:5000/parking`
2. Bấm "Chụp biển số" → Chờ timeout hoặc lỗi
3. Bấm "Nhập tay" → Nhập biển số
4. Tick "Đánh dấu xe đáng nghi ngờ"
5. Bấm "Xác nhận xe vào bãi"
6. Kiểm tra database xem dữ liệu đã lưu đúng chưa

---

## 📞 Hỗ trợ

Nếu gặp vấn đề, kiểm tra:
1. Console log trong trình duyệt (F12)
2. Flask server log
3. Database log (SQL Server Management Studio)
4. File ảnh snapshot có được lưu không

---

## 📝 Changelog

### Version 1.0 (2025-04-11)
- ✅ Thêm chế độ nhập tay với timeout 3 giây
- ✅ Bắt buộc chụp ảnh snapshot trước khi nhập tay
- ✅ Thêm checkbox đánh dấu xe nghi ngờ
- ✅ Thêm comparison view để đối chiếu
- ✅ Cập nhật database schema với 7 cột mới
- ✅ Tạo view và stored procedure cho audit trail
- ✅ Lưu ảnh snapshot vào server
- ✅ Ghi log cảnh báo cho xe nghi ngờ

---

**Tài liệu này được tạo bởi Kiro AI Assistant**

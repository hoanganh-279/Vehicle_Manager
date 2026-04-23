# 🚀 GIAI ĐOẠN 1: VÁ LỖI CORE LOGIC & DATABASE

## 📋 TỔNG QUAN

Giai đoạn này tập trung vào việc sửa các lỗi nghiêm trọng ảnh hưởng đến chức năng cốt lõi của hệ thống:

1. ✅ **Lỗi Routing** - Nút "Xem" Top 5 thẻ bị lỗi 404
2. ✅ **Lỗi Trang trắng** - Trang `/parking` không hiển thị
3. ⚠️ **Lỗi Encoding** - Font chữ tiếng Việt bị vỡ
4. ✅ **Lỗi Config** - Port MoMo không đồng bộ

---

## 🛠️ CÁC FILE ĐÃ TẠO/SỬA

### Files đã sửa:
- ✅ `admin/cards.html` - Sửa link "Xem" để truyền đúng ID thẻ

### Files công cụ mới:
- 📄 `fix_encoding_complete.py` - Script Python kiểm tra encoding database
- 📄 `fix_database_encoding.sql` - Script SQL sửa lỗi encoding
- 📄 `test_routes.py` - Script test các route bị lỗi
- 📄 `HUONG_DAN_SUA_LOI_GIAI_DOAN_1.md` - Hướng dẫn chi tiết
- 📄 `README_GIAI_DOAN_1.md` - File này

---

## 🎯 HƯỚNG DẪN THỰC HIỆN

### Bước 1: Kiểm tra Database Encoding

```bash
# Chạy script Python kiểm tra
python fix_encoding_complete.py
```

**Kết quả mong đợi:**
- Dữ liệu hiển thị đúng tiếng Việt
- Các cột text đang dùng NVARCHAR (không phải VARCHAR)

**Nếu có lỗi:**
```bash
# Chạy script SQL trong SQL Server Management Studio
# Mở file: fix_database_encoding.sql
# Đọc kỹ hướng dẫn và uncomment các lệnh ALTER TABLE nếu cần
```

---

### Bước 2: Test các Route

```bash
# Khởi động app
python app.py

# Mở terminal mới, chạy script test
python test_routes.py
```

**Kết quả mong đợi:**
```
✅ PASS - Trang Xe Vào Bãi (đã bị trắng)
✅ PASS - Trang Xe Ra Bãi
✅ PASS - Trang đăng nhập Admin
⚠️  PASS - Dashboard Admin (cần login)
⚠️  PASS - Quản lý thẻ (cần login)
⚠️  PASS - Quản lý xe (cần login)
```

---

### Bước 3: Test thủ công trên Browser

#### 3.1. Test trang /parking
```
1. Mở browser: http://localhost:5000/parking
2. Kiểm tra:
   ✓ Trang hiển thị đầy đủ (không trắng)
   ✓ Camera có thể bật
   ✓ Form nhập liệu hiển thị đúng
   ✓ Font chữ tiếng Việt hiển thị đúng
```

#### 3.2. Test nút "Xem" Top 5 thẻ
```
1. Đăng nhập admin: http://localhost:5000/admin/login
   - Email: admin@nqt.com
   - Password: admin123

2. Vào trang Quản lý người dùng: http://localhost:5000/admin/cards

3. Nhấn nút "Xem" ở Top 5 thẻ có số dư cao nhất

4. Kiểm tra:
   ✓ Chuyển đến trang chi tiết thẻ
   ✓ Không còn lỗi 404
   ✓ Thông tin thẻ hiển thị đầy đủ
```

#### 3.3. Test font chữ tiếng Việt
```
1. Vào trang Quản lý người dùng: http://localhost:5000/admin/cards

2. Kiểm tra cột "Tên Chủ Thẻ":
   ✓ Tên hiển thị đúng (VD: Nguyễn Văn A)
   ✗ Nếu hiển thị: Nguyá»...n VÄƒn A → Cần sửa database

3. Vào trang Quản lý xe: http://localhost:5000/admin/vehicles

4. Kiểm tra cột "Loại xe", "Màu biển":
   ✓ Hiển thị đúng: Xe máy, Trắng
   ✗ Nếu bị lỗi → Cần sửa database
```

---

## 🔧 SỬA LỖI ENCODING (Nếu cần)

### Phương án 1: Sửa bằng SQL Script

```sql
-- Mở SQL Server Management Studio
-- Chạy các lệnh sau:

USE ParkingManagement;
GO

-- Sửa bảng cards
ALTER TABLE cards ALTER COLUMN name NVARCHAR(255);
ALTER TABLE cards ALTER COLUMN phone NVARCHAR(20);
ALTER TABLE cards ALTER COLUMN email NVARCHAR(255);

-- Sửa bảng vehicles
ALTER TABLE vehicles ALTER COLUMN license_plate NVARCHAR(20);
ALTER TABLE vehicles ALTER COLUMN plate_color NVARCHAR(50);
ALTER TABLE vehicles ALTER COLUMN vehicle_type NVARCHAR(50);
ALTER TABLE vehicles ALTER COLUMN plate_type NVARCHAR(50);

-- Kiểm tra lại
SELECT TOP 5 name FROM cards;
SELECT TOP 5 license_plate, vehicle_type FROM vehicles;
```

### Phương án 2: Sửa dữ liệu bị lỗi

```sql
-- Nếu dữ liệu cũ đã bị lỗi, cần UPDATE lại
UPDATE cards 
SET name = N'Nguyễn Văn A' 
WHERE id = 'CARD001';

UPDATE vehicles 
SET vehicle_type = N'Xe máy',
    plate_color = N'Trắng'
WHERE id = 1;
```

---

## 🐛 TROUBLESHOOTING

### Lỗi: Trang /parking vẫn trắng

**Kiểm tra:**
```bash
# 1. Xem log trong terminal khi chạy app
python app.py
# Truy cập http://localhost:5000/parking
# Xem có lỗi gì in ra terminal không

# 2. Kiểm tra browser console
# Mở browser → F12 → Console
# Xem có lỗi JavaScript không

# 3. Kiểm tra template
# Đảm bảo file parking/entry.html tồn tại
# Đảm bảo file base.html không bị lỗi cú pháp
```

**Giải pháp:**
- Nếu lỗi 500: Kiểm tra database connection
- Nếu lỗi JavaScript: Kiểm tra file static/css/global.css
- Nếu lỗi template: Kiểm tra cú pháp Jinja2

---

### Lỗi: Nút "Xem" vẫn bị 404

**Kiểm tra:**
```python
# Mở file app.py, tìm route:
@app.route('/admin/cards/<card_id>')
@login_required
def admin_card_detail(card_id):
    # Route này phải tồn tại
```

**Giải pháp:**
- Đảm bảo route tồn tại trong app.py
- Kiểm tra ID thẻ trong database có đúng format không
- Xem log terminal khi nhấn nút "Xem"

---

### Lỗi: Font chữ vẫn bị vỡ

**Kiểm tra:**
```bash
# 1. Chạy script kiểm tra
python fix_encoding_complete.py

# 2. Xem kết quả:
# - Nếu cột là VARCHAR → Cần đổi sang NVARCHAR
# - Nếu cột là NVARCHAR → Kiểm tra dữ liệu
```

**Giải pháp:**
```sql
-- Đổi VARCHAR sang NVARCHAR
ALTER TABLE cards ALTER COLUMN name NVARCHAR(255);

-- UPDATE dữ liệu bị lỗi
UPDATE cards SET name = N'Tên đúng' WHERE id = '...';

-- Khi INSERT mới, luôn dùng N prefix
INSERT INTO cards (name) VALUES (N'Nguyễn Văn A');
```

---

### Lỗi: MoMo callback không hoạt động

**Kiểm tra:**
```bash
# 1. Kiểm tra port trong .env
cat .env | grep MOMO

# 2. Kiểm tra port app đang chạy
# Xem dòng cuối file app.py:
# app.run(debug=True, host='0.0.0.0', port=5000)

# 3. Đảm bảo port khớp nhau
```

**Giải pháp:**
```env
# File .env - Đảm bảo port khớp với app
MOMO_REDIRECT_URL=http://localhost:5000/payment/result
MOMO_IPN_URL=http://localhost:5000/payment/result
```

---

## ✅ CHECKLIST HOÀN THÀNH GIAI ĐOẠN 1

Đánh dấu ✓ vào các mục đã hoàn thành:

### Kiểm tra Database
- [ ] Chạy `python fix_encoding_complete.py` thành công
- [ ] Dữ liệu hiển thị đúng tiếng Việt
- [ ] Các cột text đang dùng NVARCHAR

### Test Routes
- [ ] Chạy `python test_routes.py` thành công
- [ ] Trang `/parking` hiển thị đúng
- [ ] Trang `/parking/exit` hiển thị đúng
- [ ] Trang `/admin/login` hoạt động

### Test Chức năng
- [ ] Nút "Xem" Top 5 thẻ hoạt động (không lỗi 404)
- [ ] Tên người dùng hiển thị đúng tiếng Việt
- [ ] Biển số xe hiển thị đúng tiếng Việt
- [ ] Loại xe, màu biển hiển thị đúng tiếng Việt

### Kiểm tra Config
- [ ] Port trong `.env` khớp với port app
- [ ] MoMo URL đúng format
- [ ] Database connection hoạt động

---

## 📊 BÁO CÁO KẾT QUẢ

Sau khi hoàn thành, hãy điền vào mẫu báo cáo này:

```
=== BÁO CÁO GIAI ĐOẠN 1 ===

1. Lỗi nút "Xem" Top 5 thẻ:
   [ ] ✅ Đã sửa
   [ ] ❌ Vẫn còn lỗi
   Ghi chú: _______________________

2. Lỗi trang /parking trắng:
   [ ] ✅ Đã sửa
   [ ] ❌ Vẫn còn lỗi
   Ghi chú: _______________________

3. Lỗi font chữ tiếng Việt:
   [ ] ✅ Đã sửa
   [ ] ❌ Vẫn còn lỗi
   Ghi chú: _______________________

4. Lỗi lệch Port MoMo:
   [ ] ✅ Đã sửa
   [ ] ❌ Vẫn còn lỗi
   Ghi chú: _______________________

Screenshot (nếu có):
- Trang /parking: _______________________
- Trang admin/cards: _______________________
- Kết quả test_routes.py: _______________________
```

---

## 🎯 BƯỚC TIẾP THEO

Sau khi hoàn thành Giai đoạn 1, hãy báo cáo kết quả để chuyển sang:

**GIAI ĐOẠN 2: Đồng bộ Giao diện & Dark/Light Mode**
- Quy chuẩn CSS Global
- Xử lý Dark Mode hoàn chỉnh
- Đồng bộ trang "Xe ra bãi"

---

## 📞 HỖ TRỢ

Nếu gặp vấn đề, hãy cung cấp:
1. Log lỗi từ terminal
2. Screenshot trang bị lỗi
3. Kết quả chạy `python fix_encoding_complete.py`
4. Kết quả chạy `python test_routes.py`

**Chúc bạn thành công! 🚀**

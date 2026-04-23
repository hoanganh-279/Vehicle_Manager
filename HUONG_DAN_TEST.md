# 🧪 HƯỚNG DẪN TEST CHI TIẾT - GIAI ĐOẠN 1

## 📋 CHUẨN BỊ

### Yêu cầu:
- ✅ Python đã cài đặt
- ✅ SQL Server đang chạy
- ✅ Database ParkingManagement đã tạo
- ✅ Các package Python đã cài: `pip install -r requirements.txt`

---

## 🚀 TEST 1: NÚT "XEM" TOP 5 THẺ

### Mục tiêu:
Kiểm tra nút "Xem" ở Top 5 thẻ có số dư cao nhất không còn bị lỗi 404

### Các bước:

#### Bước 1: Khởi động app
```bash
python app.py
```

**Kết quả mong đợi:**
```
 * Running on http://0.0.0.0:5000
 * Running on http://127.0.0.1:5000
```

#### Bước 2: Đăng nhập Admin
1. Mở browser: `http://localhost:5000/admin/login`
2. Nhập thông tin:
   - Email: `admin@nqt.com`
   - Password: `admin123`
3. Nhấn "Đăng nhập"

**Kết quả mong đợi:**
- ✅ Chuyển đến trang Dashboard
- ✅ Không có thông báo lỗi

#### Bước 3: Vào trang Quản lý người dùng
1. Click menu "Quản lý người dùng" hoặc truy cập: `http://localhost:5000/admin/cards`

**Kết quả mong đợi:**
- ✅ Trang hiển thị danh sách thẻ
- ✅ Có phần "Top 5 thẻ có số dư cao nhất"
- ✅ Font chữ tiếng Việt hiển thị đúng (nếu có dữ liệu)

#### Bước 4: Test nút "Xem"
1. Tìm phần "Top 5 thẻ có số dư cao nhất"
2. Nhấn nút "Xem" (icon mắt) ở bất kỳ thẻ nào

**Kết quả mong đợi:**
- ✅ Chuyển đến trang chi tiết thẻ
- ✅ URL dạng: `http://localhost:5000/admin/cards/CARD-XXX-...`
- ✅ Trang hiển thị thông tin chi tiết thẻ
- ❌ KHÔNG còn lỗi 404 Not Found

#### Bước 5: Kiểm tra trong bảng danh sách
1. Scroll xuống bảng "Danh sách thẻ (30 thẻ mới nhất)"
2. Nhấn nút "Xem" (icon mắt) ở bất kỳ thẻ nào

**Kết quả mong đợi:**
- ✅ Chuyển đến trang chi tiết thẻ
- ✅ Không có lỗi 404

### ✅ Test thành công nếu:
- [x] Nút "Xem" ở Top 5 thẻ hoạt động
- [x] Nút "Xem" trong bảng danh sách hoạt động
- [x] Không còn lỗi 404
- [x] Trang chi tiết thẻ hiển thị đúng

### ❌ Nếu vẫn lỗi:
1. Xem log trong terminal
2. Kiểm tra URL có đúng format không
3. Kiểm tra route `/admin/cards/<card_id>` trong app.py
4. Báo cáo lỗi với screenshot

---

## 🚀 TEST 2: TRANG /PARKING

### Mục tiêu:
Kiểm tra trang "Xe Vào Bãi" không còn bị trắng

### Các bước:

#### Bước 1: Truy cập trang
1. Mở browser: `http://localhost:5000/parking`

**Kết quả mong đợi:**
- ✅ Trang hiển thị đầy đủ
- ✅ Có header "NQT Parking — Xe Vào Bãi"
- ✅ Có phần camera nhận diện biển số
- ✅ Có form nhập thông tin xe
- ✅ Có thống kê chỗ trống (Xe máy/Xe hơi)

#### Bước 2: Kiểm tra các thành phần

**2.1. Kiểm tra Header:**
- ✅ Logo "NQT Parking — Xe Vào Bãi"
- ✅ Thống kê xe máy: "X/Y"
- ✅ Thống kê xe hơi: "X/Y"
- ✅ Nút "Admin" để quay lại

**2.2. Kiểm tra Steps:**
- ✅ Bước 1: Nhận diện (active)
- ✅ Bước 2: Xác nhận
- ✅ Bước 3: Hoàn tất

**2.3. Kiểm tra Camera:**
- ✅ Khung camera hiển thị
- ✅ Dropdown chọn camera
- ✅ Nút "Chụp biển số"
- ✅ Nút "Nhập tay biển số"

**2.4. Kiểm tra Form bên phải:**
- ✅ Input "Biển số xe"
- ✅ Select "Loại xe"
- ✅ Select "Màu biển"
- ✅ Select "Loại biển"
- ✅ Input "Mã thẻ thành viên"
- ✅ Nút "Xác nhận xe vào bãi"

#### Bước 3: Test chức năng cơ bản

**3.1. Test nhập tay:**
1. Click "Nhập tay biển số"
2. Nhập biển số: `51A-123.45`
3. Chọn loại xe: `Xe máy`
4. Click "Dùng thông tin này"

**Kết quả mong đợi:**
- ✅ Biển số xuất hiện trong form bên phải
- ✅ Chuyển sang Bước 2

**3.2. Test xác nhận:**
1. Click nút "Xác nhận xe vào bãi"

**Kết quả mong đợi:**
- ✅ Hiển thị thông báo thành công
- ✅ Chuyển sang Bước 3
- ✅ Hiển thị thông tin xe đã vào bãi

### ✅ Test thành công nếu:
- [x] Trang hiển thị đầy đủ (không trắng)
- [x] Tất cả thành phần hiển thị đúng
- [x] Font chữ tiếng Việt hiển thị đúng
- [x] Có thể nhập tay biển số
- [x] Có thể xác nhận xe vào bãi

### ❌ Nếu trang vẫn trắng:

**Kiểm tra 1: Log trong terminal**
```bash
# Xem log khi truy cập trang
# Tìm dòng có "GET /parking"
# Xem có lỗi gì không
```

**Kiểm tra 2: Browser Console**
```bash
# Mở F12 → Console
# Xem có lỗi JavaScript không
# Xem có lỗi load CSS/Font không
```

**Kiểm tra 3: Database Connection**
```bash
# Chạy script kiểm tra
python fix_encoding_complete.py

# Nếu lỗi connection:
# - Kiểm tra SQL Server có chạy không
# - Kiểm tra tên server trong .env
# - Kiểm tra database đã tạo chưa
```

**Kiểm tra 4: Clear Cache**
```bash
# Trong browser:
# Ctrl+Shift+Delete
# Chọn "Cached images and files"
# Clear
# Reload trang (Ctrl+F5)
```

---

## 🚀 TEST 3: FONT CHỮ TIẾNG VIỆT

### Mục tiêu:
Kiểm tra font chữ tiếng Việt hiển thị đúng trong tất cả trang

### Các bước:

#### Bước 1: Test trang Quản lý người dùng
1. Truy cập: `http://localhost:5000/admin/cards`
2. Kiểm tra cột "Tên Chủ Thẻ"

**Kết quả mong đợi:**
- ✅ Tên hiển thị đúng: "Nguyễn Văn A"
- ❌ KHÔNG hiển thị: "Nguyá»...n VÄƒn A"

#### Bước 2: Test trang Quản lý xe
1. Truy cập: `http://localhost:5000/admin/vehicles`
2. Kiểm tra cột "Loại xe", "Màu biển"

**Kết quả mong đợi:**
- ✅ Loại xe: "Xe máy", "Xe hơi"
- ✅ Màu biển: "Trắng", "Vàng", "Xanh"
- ❌ KHÔNG bị lỗi font

#### Bước 3: Test trang Xe vào bãi
1. Truy cập: `http://localhost:5000/parking`
2. Kiểm tra các label, button

**Kết quả mong đợi:**
- ✅ Tất cả chữ tiếng Việt hiển thị đúng
- ✅ Font "Be Vietnam Pro" load thành công

### ✅ Test thành công nếu:
- [x] Tên người dùng hiển thị đúng
- [x] Loại xe, màu biển hiển thị đúng
- [x] Tất cả label, button hiển thị đúng
- [x] Không có ký tự lạ

### ❌ Nếu vẫn bị lỗi font:

**Giải pháp 1: Kiểm tra Database**
```bash
# Chạy script kiểm tra
python fix_encoding_complete.py

# Xem kết quả:
# - Nếu cột là VARCHAR → Cần đổi sang NVARCHAR
# - Nếu cột là NVARCHAR → Kiểm tra dữ liệu
```

**Giải pháp 2: Sửa Database**
```sql
-- Mở SQL Server Management Studio
-- Chạy file: fix_database_encoding.sql
-- Hoặc chạy trực tiếp:

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

**Giải pháp 3: UPDATE dữ liệu cũ**
```sql
-- Nếu dữ liệu cũ đã bị lỗi
UPDATE cards 
SET name = N'Nguyễn Văn A' 
WHERE id = 'CARD001';

UPDATE vehicles 
SET vehicle_type = N'Xe máy',
    plate_color = N'Trắng'
WHERE id = 1;
```

**Giải pháp 4: Kiểm tra Font**
```bash
# Mở F12 → Network
# Reload trang (Ctrl+F5)
# Tìm "Be Vietnam Pro"
# Xem có load thành công không
```

---

## 🚀 TEST 4: DARK MODE

### Mục tiêu:
Kiểm tra Dark Mode có hoạt động không (sẽ sửa hoàn chỉnh ở Giai đoạn 2)

### Các bước:

#### Bước 1: Bật Dark Mode
1. Vào bất kỳ trang Admin nào
2. Click icon mặt trăng ở góc trên bên trái (trong logo)

**Kết quả hiện tại:**
- ✅ Sidebar chuyển sang màu tối
- ⚠️ Content vẫn màu trắng (sẽ sửa ở Giai đoạn 2)

#### Bước 2: Tắt Dark Mode
1. Click icon mặt trời

**Kết quả mong đợi:**
- ✅ Sidebar chuyển về màu gradient tím
- ✅ Content vẫn màu trắng

### ✅ Test thành công nếu:
- [x] Nút toggle Dark Mode hoạt động
- [x] Sidebar đổi màu khi bật/tắt
- [x] Không có lỗi JavaScript

### ⚠️ Lưu ý:
- Dark Mode chưa hoàn chỉnh (Content chưa đổi màu)
- Sẽ được sửa hoàn chỉnh ở Giai đoạn 2

---

## 📊 BẢNG TỔNG HỢP KẾT QUẢ TEST

| Test | Mục tiêu | Kết quả | Ghi chú |
|------|----------|---------|---------|
| 1. Nút "Xem" Top 5 thẻ | Không lỗi 404 | [ ] Pass / [ ] Fail | |
| 2. Trang /parking | Hiển thị đầy đủ | [ ] Pass / [ ] Fail | |
| 3. Font tiếng Việt | Hiển thị đúng | [ ] Pass / [ ] Fail | |
| 4. Dark Mode | Toggle hoạt động | [ ] Pass / [ ] Fail | |

---

## 📝 MẪU BÁO CÁO KẾT QUẢ

```
=== BÁO CÁO TEST GIAI ĐOẠN 1 ===

Ngày test: __________
Người test: __________

1. Nút "Xem" Top 5 thẻ:
   [ ] ✅ Pass - Hoạt động bình thường
   [ ] ❌ Fail - Vẫn lỗi 404
   Ghi chú: _______________________

2. Trang /parking:
   [ ] ✅ Pass - Hiển thị đầy đủ
   [ ] ❌ Fail - Vẫn trắng
   Ghi chú: _______________________

3. Font tiếng Việt:
   [ ] ✅ Pass - Hiển thị đúng
   [ ] ❌ Fail - Vẫn bị lỗi
   Ghi chú: _______________________

4. Dark Mode:
   [ ] ✅ Pass - Toggle hoạt động
   [ ] ❌ Fail - Không hoạt động
   Ghi chú: _______________________

Screenshot đính kèm:
- Trang /parking: _______________________
- Trang admin/cards: _______________________
- Log lỗi (nếu có): _______________________

Kết luận:
_______________________________________
_______________________________________
```

---

## 🎯 TIÊU CHÍ PASS/FAIL

### ✅ PASS - Giai đoạn 1 hoàn thành nếu:
- [x] Nút "Xem" Top 5 thẻ hoạt động (không lỗi 404)
- [x] Trang /parking hiển thị đầy đủ (không trắng)
- [x] Font tiếng Việt hiển thị đúng (hoặc đã có hướng dẫn sửa)
- [x] Dark Mode toggle hoạt động (dù chưa hoàn chỉnh)

### ❌ FAIL - Cần sửa thêm nếu:
- [ ] Nút "Xem" vẫn lỗi 404
- [ ] Trang /parking vẫn trắng
- [ ] Font tiếng Việt vẫn bị lỗi sau khi sửa database
- [ ] Dark Mode không hoạt động

---

## 📞 HỖ TRỢ

Nếu gặp vấn đề khi test, hãy cung cấp:

1. **Log lỗi từ terminal:**
   ```bash
   # Copy toàn bộ log khi chạy python app.py
   ```

2. **Screenshot trang bị lỗi:**
   - Chụp toàn bộ trang
   - Chụp cả URL bar

3. **Browser Console log:**
   ```bash
   # Mở F12 → Console
   # Copy tất cả lỗi màu đỏ
   ```

4. **Kết quả script kiểm tra:**
   ```bash
   # Nếu chạy được:
   python fix_encoding_complete.py
   # Copy kết quả
   ```

---

**Chúc bạn test thành công! 🎉**

Sau khi test xong, báo cáo kết quả để chuyển sang Giai đoạn 2.

# 🔧 HƯỚNG DẪN SỬA LỖI - GIAI ĐOẠN 1

## ✅ CÁC LỖI ĐÃ ĐƯỢC SỬA

### 1. ✅ Lỗi nút "Xem" ở Top 5 thẻ
**Nguyên nhân:** Template đang cắt ID thẻ chỉ lấy 8 ký tự đầu (`card.id[:8]`) nhưng route cần ID đầy đủ.

**Đã sửa:** 
- File `admin/cards.html` - Dòng link "Xem" đã được sửa thành `url_for('admin_card_detail', card_id=card.id)` để truyền đúng ID đầy đủ
- Thêm kiểm tra độ dài ID trước khi cắt để hiển thị

**Cách test:**
```bash
1. Chạy app: python app.py
2. Truy cập: http://localhost:5000/admin/cards
3. Nhấn nút "Xem" ở Top 5 thẻ
4. Kết quả mong đợi: Chuyển đến trang chi tiết thẻ, không còn lỗi 404
```

---

### 2. ✅ Lỗi trang /parking trắng
**Nguyên nhân:** Template `parking/entry.html` extends `base.html` đúng, route đã có, nhưng có thể thiếu font hoặc CSS.

**Đã kiểm tra:**
- ✓ Route `/parking` đã có trong `app.py` (dòng 1350)
- ✓ Template `parking/entry.html` tồn tại và cú pháp đúng
- ✓ File `base.html` đúng cú pháp, có meta charset UTF-8

**Cách test:**
```bash
1. Chạy app: python app.py
2. Truy cập: http://localhost:5000/parking
3. Kết quả mong đợi: Hiển thị trang "Xe Vào Bãi" với camera và form
```

**Nếu vẫn trắng, kiểm tra:**
```bash
# Xem log lỗi trong terminal khi chạy app
python app.py

# Kiểm tra browser console (F12) xem có lỗi JavaScript không
```

---

### 3. ⚠️ Lỗi Font chữ tiếng Việt (CẦN KIỂM TRA DATABASE)

**Nguyên nhân có thể:**
- Database đang dùng VARCHAR thay vì NVARCHAR
- Dữ liệu cũ đã bị lưu sai encoding
- Khi INSERT không dùng N'...' prefix

**Công cụ kiểm tra:**
Tôi đã tạo script `fix_encoding_complete.py` để kiểm tra:

```bash
# Chạy script kiểm tra
python fix_encoding_complete.py
```

**Script sẽ kiểm tra:**
1. ✓ Dữ liệu hiện tại có hiển thị đúng tiếng Việt không
2. ✓ Collation của database
3. ✓ Kiểu dữ liệu các cột (VARCHAR vs NVARCHAR)
4. ✓ Đưa ra khuyến nghị sửa lỗi

**Nếu script báo lỗi VARCHAR:**

```sql
-- Ví dụ: Chuyển cột name trong bảng cards từ VARCHAR sang NVARCHAR
ALTER TABLE cards ALTER COLUMN name NVARCHAR(255);
ALTER TABLE cards ALTER COLUMN phone NVARCHAR(20);
ALTER TABLE cards ALTER COLUMN email NVARCHAR(255);

-- Tương tự cho bảng vehicles
ALTER TABLE vehicles ALTER COLUMN license_plate NVARCHAR(20);
ALTER TABLE vehicles ALTER COLUMN plate_color NVARCHAR(50);
ALTER TABLE vehicles ALTER COLUMN vehicle_type NVARCHAR(50);
```

**Khi INSERT dữ liệu mới, LUÔN dùng N'...':**
```python
# SAI - sẽ bị lỗi font
execute_db("INSERT INTO cards (name) VALUES (?)", ["Nguyễn Văn A"])

# ĐÚNG - dùng N prefix trong SQL
execute_db("INSERT INTO cards (name) VALUES (N?)", ["Nguyễn Văn A"])

# HOẶC đảm bảo connection đã set encoding đúng (đã có trong app.py)
conn.setencoding(encoding='utf-16-le')
```

---

### 4. ✅ Lỗi lệch Port MoMo

**Nguyên nhân:** File `.env` đang cấu hình:
- `MOMO_REDIRECT_URL=http://localhost:5000/payment/result`
- `MOMO_IPN_URL=http://localhost:5000/payment/result`

Nhưng app có thể đang chạy port khác (5172, 5001).

**Đã kiểm tra:**
- ✓ File `app.py` dòng cuối: `app.run(debug=True, host='0.0.0.0', port=5000)`
- ✓ File `.env` đã đúng port 5000

**Cách sửa nếu muốn đổi port:**

1. Đổi port trong `app.py`:
```python
# Dòng cuối cùng của app.py
if __name__ == '__main__':
    os.makedirs(os.path.join('static', 'uploads'), exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5172)  # Đổi thành port bạn muốn
```

2. Đổi port trong `.env`:
```env
MOMO_REDIRECT_URL=http://localhost:5172/payment/result
MOMO_IPN_URL=http://localhost:5172/payment/result
VNPAY_RETURN_URL=http://localhost:5172/payment/result
```

**QUAN TRỌNG:** Tất cả URL phải cùng port!

---

## 📋 CHECKLIST KIỂM TRA SAU KHI SỬA

### Bước 1: Kiểm tra Database Encoding
```bash
python fix_encoding_complete.py
```
- [ ] Script chạy thành công
- [ ] Dữ liệu hiển thị đúng tiếng Việt
- [ ] Các cột text đang dùng NVARCHAR (không phải VARCHAR)

### Bước 2: Test các trang bị lỗi
```bash
# Khởi động app
python app.py
```

- [ ] Trang `/parking` hiển thị đúng (không còn trắng)
- [ ] Nút "Xem" ở Top 5 thẻ hoạt động (không còn lỗi 404)
- [ ] Trang `/admin/cards` hiển thị tên tiếng Việt đúng
- [ ] Trang `/admin/vehicles` hiển thị biển số tiếng Việt đúng

### Bước 3: Test thanh toán MoMo (nếu có tài khoản test)
- [ ] Port trong `.env` khớp với port app đang chạy
- [ ] Tạo giao dịch test và kiểm tra callback

---

## 🚨 NẾU VẪN CÒN LỖI

### Lỗi font chữ vẫn bị vỡ:
1. Chạy `python fix_encoding_complete.py` và đọc kỹ kết quả
2. Nếu cột đang là VARCHAR, chạy lệnh ALTER TABLE (xem phần 3 ở trên)
3. Xóa dữ liệu test cũ và INSERT lại với N'...' prefix
4. Kiểm tra browser có load đúng font "Be Vietnam Pro" không (F12 → Network)

### Trang /parking vẫn trắng:
1. Mở browser console (F12) xem lỗi JavaScript
2. Kiểm tra terminal xem có lỗi Python không
3. Thử truy cập trực tiếp: `http://localhost:5000/parking`
4. Kiểm tra file `parking/entry.html` có lỗi cú pháp không

### Nút "Xem" vẫn lỗi:
1. Kiểm tra route `/admin/cards/<card_id>` có tồn tại trong `app.py` không
2. Xem log terminal khi nhấn nút
3. Kiểm tra ID thẻ trong database có đúng format không

---

## 📞 HỖ TRỢ

Sau khi test xong, hãy cho tôi biết:
1. ✅ Những lỗi nào đã được sửa
2. ❌ Những lỗi nào vẫn còn
3. 📸 Screenshot hoặc log lỗi (nếu có)

Sau đó tôi sẽ chuyển sang **GIAI ĐOẠN 2: Đồng bộ Giao diện & Dark/Light Mode**

---

## 🎯 TÓM TẮT GIAI ĐOẠN 1

| Lỗi | Trạng thái | Cần làm gì |
|-----|-----------|-----------|
| Nút "Xem" Top 5 thẻ | ✅ Đã sửa | Test lại |
| Trang /parking trắng | ✅ Đã kiểm tra | Test lại |
| Font tiếng Việt | ⚠️ Cần kiểm tra DB | Chạy `fix_encoding_complete.py` |
| Lệch Port MoMo | ✅ Đã kiểm tra | Đảm bảo port đồng bộ |

**Hãy test và báo kết quả để tôi tiếp tục Giai đoạn 2!** 🚀

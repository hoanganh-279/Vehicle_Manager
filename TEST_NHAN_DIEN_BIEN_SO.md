# Hướng Dẫn Test Nhận Diện Biển Số

## Vấn đề hiện tại
Hệ thống không nhận diện được biển số từ camera.

## Nguyên nhân chính
1. **Chất lượng ảnh từ camera**: Ảnh từ webcam thường có độ phân giải thấp, nhiễu, thiếu sáng
2. **Góc chụp**: Camera không vuông góc với biển số
3. **Khoảng cách**: Biển số quá nhỏ trong khung hình
4. **Tesseract OCR**: Chỉ hoạt động tốt với ảnh chất lượng cao, rõ nét

## Giải pháp đã cải thiện

### 1. Loại bỏ YOLO
- YOLO model tổng quát không được train cho biển số Việt Nam
- Giờ xử lý trực tiếp toàn bộ ảnh bằng Tesseract

### 2. Cải thiện tiền xử lý
- Resize ảnh lên 200px chiều cao
- Thử nhiều phương pháp threshold (binary, inverse)
- Thử nhiều PSM mode của Tesseract

### 3. Thêm format biển số
- Tự động format: `99E122268` → `99-E1 222.68`
- Hỗ trợ nhiều format biển số Việt Nam

## Cách test

### Test 1: Với ảnh có sẵn
```bash
# Chụp ảnh biển số rõ nét, lưu vào file
# Sau đó chạy:
python test_ocr.py plate.jpg
```

### Test 2: Trên web
1. Mở trình duyệt: http://localhost:5000/parking
2. Bật camera
3. Đưa biển số vào khung hình (chiếm ít nhất 70% khung hình)
4. Đảm bảo:
   - Đủ ánh sáng
   - Biển số rõ nét, không mờ
   - Vuông góc với camera
5. Click "Chụp biển số"

### Test 3: Debug mode
Thêm log vào `app.py` route `/recognize_plate`:

```python
@app.route('/recognize_plate', methods=['POST'])
def recognize_plate():
    # ... existing code ...
    
    # Thêm log
    print(f"Received image size: {frame.shape}")
    print(f"Detected plate: {plate_text}")
    print(f"Confidence: {confidence}")
    
    # ... rest of code ...
```

## Tips để tăng tỷ lệ nhận diện

### 1. Điều kiện lý tưởng
✅ Ánh sáng tự nhiên ban ngày  
✅ Biển số sạch, không bị bẩn  
✅ Camera vuông góc với biển số  
✅ Biển số chiếm 70-80% khung hình  
✅ Giữ camera ổn định 1-2 giây  

### 2. Điều kiện tránh
❌ Ánh sáng yếu, tối  
❌ Biển số bị mờ, bẩn  
❌ Góc chụp nghiêng >30°  
❌ Biển số quá nhỏ (<30% khung hình)  
❌ Camera rung lắc  

### 3. Khoảng cách tối ưu
- **Xe máy**: 0.5 - 1.5 mét
- **Xe hơi**: 1 - 2 mét

### 4. Độ phân giải camera
- Tối thiểu: 640x480
- Khuyến nghị: 1280x720 (HD)
- Tốt nhất: 1920x1080 (Full HD)

## Nếu vẫn không nhận diện được

### Giải pháp 1: Nhập tay
1. Click "Nhập tay biển số"
2. Nhập biển số: `99-E1 222.68`
3. Chọn loại xe, màu biển
4. Click "Dùng thông tin này"

### Giải pháp 2: Sử dụng ảnh chất lượng cao
1. Chụp ảnh biển số bằng điện thoại (độ phân giải cao)
2. Chuyển ảnh sang máy tính
3. Test bằng script: `python test_ocr.py plate.jpg`
4. Nếu nhận diện được → vấn đề là chất lượng camera
5. Nếu không nhận diện được → vấn đề là thuật toán

### Giải pháp 3: Nâng cấp
Để tăng độ chính xác lên 90%+, cần:
- Sử dụng model AI chuyên dụng (YOLOv8 trained trên biển số VN)
- Hoặc sử dụng EasyOCR (hỗ trợ tiếng Việt tốt hơn)
- Camera chất lượng cao (1080p+)
- Đèn LED hỗ trợ ánh sáng

## Ví dụ format biển số hỗ trợ

### Xe máy
- `51A-123.45` ✅
- `51A12345` ✅ (tự động format thành `51A-123.45`)
- `30B-456.78` ✅

### Xe hơi
- `99-E1 222.68` ✅
- `99E122268` ✅ (tự động format thành `99-E1 222.68`)
- `51F-123.45` ✅

## Log lỗi thường gặp

### Lỗi 1: "Không phát hiện biển số"
**Nguyên nhân**: Tesseract không đọc được text  
**Giải pháp**: Cải thiện chất lượng ảnh, ánh sáng

### Lỗi 2: "Không thể đọc ảnh"
**Nguyên nhân**: File ảnh bị lỗi hoặc format không hỗ trợ  
**Giải pháp**: Kiểm tra file ảnh, thử format khác (JPG, PNG)

### Lỗi 3: Nhận diện sai ký tự
**Nguyên nhân**: OCR nhầm lẫn (0→O, 1→I, 8→B)  
**Giải pháp**: Cải thiện tiền xử lý, hoặc nhập tay

## Kết luận
Hệ thống OCR đơn giản có độ chính xác 50-70% trong điều kiện lý tưởng. Để đạt 90%+, cần đầu tư vào model AI chuyên dụng hoặc camera chất lượng cao.

Trong thời gian chờ nâng cấp, khuyến nghị sử dụng chức năng "Nhập tay biển số" để đảm bảo hệ thống hoạt động ổn định.

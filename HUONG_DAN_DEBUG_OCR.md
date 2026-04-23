# Hướng Dẫn Debug OCR Không Nhận Diện Được Biển Số

## Vấn đề
Hệ thống không nhận diện được biển số xe từ camera.

## Nguyên nhân có thể

### 1. Chất lượng ảnh kém
- Ảnh mờ, thiếu sáng
- Góc chụp không vuông góc
- Biển số bị che khuất
- Khoảng cách quá xa hoặc quá gần

### 2. Cấu hình Tesseract
- Tesseract chưa được cài đặt đúng
- Đường dẫn không chính xác
- Thiếu ngôn ngữ tiếng Anh (eng.traineddata)

### 3. Tiền xử lý ảnh
- Ảnh chưa được xử lý tốt (contrast, brightness)
- Kích thước ảnh quá nhỏ

## Cách khắc phục

### Bước 1: Kiểm tra Tesseract
```bash
# Kiểm tra Tesseract đã cài đặt
tesseract --version

# Kiểm tra ngôn ngữ có sẵn
tesseract --list-langs
```

### Bước 2: Test OCR với ảnh mẫu
```bash
# Chụp ảnh biển số và lưu vào file
# Sau đó test:
python test_ocr.py plate.jpg
```

### Bước 3: Cải thiện chất lượng ảnh
- Đảm bảo đủ ánh sáng
- Chụp vuông góc với biển số
- Zoom vào biển số (biển số chiếm ít nhất 50% khung hình)
- Giữ camera ổn định, không rung

### Bước 4: Điều chỉnh camera
Trong file `parking/entry.html`, camera được cấu hình:
- Resolution: 1280x720
- Có thể thử resolution cao hơn nếu camera hỗ trợ

### Bước 5: Sử dụng ảnh test
Thay vì dùng camera, có thể upload ảnh biển số trực tiếp:
1. Chụp ảnh biển số rõ nét
2. Lưu vào `static/uploads/test_plate.jpg`
3. Test bằng script `test_ocr.py`

## Tips để tăng độ chính xác

### 1. Điều kiện ánh sáng
- Ánh sáng tự nhiên ban ngày: TỐT NHẤT
- Đèn LED trắng: TỐT
- Đèn huỳnh quang: TRUNG BÌNH
- Ánh sáng vàng/tối: KÉM

### 2. Góc chụp
- Vuông góc (0°): TỐT NHẤT
- Nghiêng 15-30°: TRUNG BÌNH
- Nghiêng >30°: KÉM

### 3. Khoảng cách
- 1-2 mét: TỐT NHẤT
- 0.5-1 mét: TỐT
- >3 mét: KÉM (biển số quá nhỏ)
- <0.5 mét: KÉM (biển số quá gần)

### 4. Format biển số Việt Nam
Hệ thống nhận diện các format:
- `51A-123.45` (xe máy)
- `51A-12345` (xe máy)
- `99-E1 222.68` (xe hơi)
- `30A-123.45` (xe máy)

## Nếu vẫn không hoạt động

### Giải pháp tạm thời: Nhập tay
1. Click nút "Nhập tay biển số"
2. Nhập biển số thủ công
3. Chọn loại xe, màu biển
4. Click "Dùng thông tin này"

### Nâng cấp trong tương lai
- Sử dụng model AI chuyên dụng cho biển số Việt Nam
- Tích hợp EasyOCR (hỗ trợ tiếng Việt tốt hơn)
- Sử dụng camera chất lượng cao hơn
- Thêm đèn LED hỗ trợ ánh sáng

## Liên hệ hỗ trợ
Nếu vẫn gặp vấn đề, vui lòng cung cấp:
1. Screenshot màn hình lỗi
2. Ảnh biển số đang test
3. Log lỗi từ console (F12 > Console)

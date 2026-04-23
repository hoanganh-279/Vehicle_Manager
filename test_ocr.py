"""
Script test OCR đơn giản để kiểm tra Tesseract
"""
import cv2
import pytesseract
import sys

# Cấu hình Tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def test_ocr(image_path):
    """Test OCR trên một ảnh"""
    print(f"Đang test OCR trên: {image_path}")
    
    # Đọc ảnh
    img = cv2.imread(image_path)
    if img is None:
        print("Không thể đọc ảnh!")
        return
    
    print(f"Kích thước ảnh: {img.shape}")
    
    # Chuyển sang grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Thử nhiều config
    configs = [
        ('PSM 7 - Single line', '--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789ABCDEFGHKLMNPRSTUVXYZ-.'),
        ('PSM 8 - Single word', '--oem 3 --psm 8 -c tessedit_char_whitelist=0123456789ABCDEFGHKLMNPRSTUVXYZ-.'),
        ('PSM 6 - Block', '--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHKLMNPRSTUVXYZ-.'),
        ('PSM 11 - Sparse', '--oem 3 --psm 11 -c tessedit_char_whitelist=0123456789ABCDEFGHKLMNPRSTUVXYZ-.'),
    ]
    
    print("\n=== KẾT QUẢ NHẬN DIỆN ===")
    for name, config in configs:
        try:
            text = pytesseract.image_to_string(gray, config=config, lang='eng')
            text = text.strip().upper()
            print(f"{name}: '{text}'")
        except Exception as e:
            print(f"{name}: LỖI - {e}")
    
    # Thử với ảnh gốc
    print("\n=== THỬ VỚI ẢNH GỐC (màu) ===")
    try:
        text = pytesseract.image_to_string(img, config='--oem 3 --psm 7', lang='eng')
        print(f"Kết quả: '{text.strip()}'")
    except Exception as e:
        print(f"LỖI: {e}")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        test_ocr(sys.argv[1])
    else:
        print("Cách dùng: python test_ocr.py <đường_dẫn_ảnh>")
        print("Ví dụ: python test_ocr.py plate.jpg")

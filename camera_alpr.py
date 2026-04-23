"""
Real-time ALPR (Automatic License Plate Recognition) Module
Sử dụng Tesseract OCR để nhận diện biển số xe Việt Nam
"""

import cv2
import numpy as np
import pytesseract
import os
from datetime import datetime
import re

class LicensePlateDetector:
    def __init__(self, model_path='yolov8n.pt', upload_folder='static/uploads'):
        """
        Khởi tạo detector
        Args:
            model_path: Đường dẫn đến model YOLO (không dùng trong phiên bản này)
            upload_folder: Thư mục lưu ảnh
        """
        self.upload_folder = upload_folder
        
        # Tạo thư mục uploads nếu chưa có
        os.makedirs(upload_folder, exist_ok=True)
        
        # Cấu hình Tesseract — đọc từ biến môi trường (LOCAL=Windows, Render=Linux)
        tesseract_path = os.getenv('TESSERACT_PATH', '/usr/bin/tesseract')
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
        
    def preprocess_plate(self, plate_img):
        """
        Tiền xử lý ảnh biển số để OCR tốt hơn
        """
        # Resize để tăng độ phân giải
        height, width = plate_img.shape[:2]
        if height < 200:
            scale = 200 / height
            plate_img = cv2.resize(plate_img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        
        # Convert to grayscale
        gray = cv2.cvtColor(plate_img, cv2.COLOR_BGR2GRAY)
        
        # Apply bilateral filter to reduce noise while keeping edges sharp
        gray = cv2.bilateralFilter(gray, 11, 17, 17)
        
        # Apply adaptive threshold
        thresh = cv2.adaptiveThreshold(
            gray, 255, 
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 
            11, 2
        )
        
        # Thử cả ảnh âm bản (invert)
        thresh_inv = cv2.bitwise_not(thresh)
        
        # Morphological operations
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        thresh_inv = cv2.morphologyEx(thresh_inv, cv2.MORPH_CLOSE, kernel)
        
        return gray, thresh, thresh_inv
        
        return thresh
    
    def extract_text_tesseract(self, plate_img):
        """
        Trích xuất text từ ảnh biển số bằng Tesseract
        Thử nhiều cấu hình khác nhau để tăng độ chính xác
        """
        # Preprocess
        gray, thresh, thresh_inv = self.preprocess_plate(plate_img)
        
        # Thử nhiều config khác nhau
        configs = [
            r'--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789ABCDEFGHKLMNPRSTUVXYZ-.',
            r'--oem 3 --psm 8 -c tessedit_char_whitelist=0123456789ABCDEFGHKLMNPRSTUVXYZ-.',
            r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHKLMNPRSTUVXYZ-.',
        ]
        
        images_to_try = [gray, thresh, thresh_inv, plate_img]
        
        best_text = ""
        best_confidence = 0
        
        for img in images_to_try:
            for config in configs:
                try:
                    # OCR
                    text = pytesseract.image_to_string(img, config=config, lang='eng')
                    
                    # Clean text
                    text = text.strip().upper()
                    text = re.sub(r'[^0-9A-Z\-\.]', '', text)
                    
                    # Validate
                    if self.validate_plate_format(text) and len(text) > len(best_text):
                        best_text = text
                        
                except Exception as e:
                    continue
        
        return best_text
    
    def validate_plate_format(self, text):
        """
        Kiểm tra format biển số Việt Nam
        Formats: 51A-123.45, 51A12345, 99-E1 222.68, etc.
        """
        if not text or len(text) < 5:
            return False
        
        # Remove spaces and dots for validation
        clean_text = text.replace(' ', '').replace('.', '').replace('-', '')
        
        # Basic validation: should have numbers and letters
        has_numbers = any(c.isdigit() for c in clean_text)
        has_letters = any(c.isalpha() for c in clean_text)
        
        # Length check (Vietnamese plates typically 6-10 characters without separators)
        valid_length = 5 <= len(clean_text) <= 12
        
        # Check for common patterns
        # Pattern 1: 51A12345 (2 digits + 1 letter + 4-5 digits)
        # Pattern 2: 99E122268 (2 digits + 1-2 letters + 5-6 digits)
        import re
        patterns = [
            r'^\d{2}[A-Z]{1,2}\d{4,6}$',  # 51A1234, 99E12345
            r'^\d{2}[A-Z]{1}\d{3}\d{2}$',  # 51A12345
        ]
        
        for pattern in patterns:
            if re.match(pattern, clean_text):
                return True
        
        # Fallback: basic check
        return has_numbers and has_letters and valid_length
    
    def format_plate_text(self, text):
        """
        Format biển số theo chuẩn Việt Nam
        Input: 99E122268 hoặc 51A12345
        Output: 99-E1 222.68 hoặc 51A-123.45
        """
        if not text:
            return text
        
        # Remove existing separators
        clean = text.replace(' ', '').replace('.', '').replace('-', '')
        
        # Try to detect format
        import re
        
        # Format 1: 2 digits + 1-2 letters + 6 digits (xe hơi)
        # Example: 99E122268 -> 99-E1 222.68
        match = re.match(r'^(\d{2})([A-Z]{1,2})(\d{6})$', clean)
        if match:
            prefix, letters, numbers = match.groups()
            # Split letters if 2 letters
            if len(letters) == 2:
                return f"{prefix}-{letters[0]}{letters[1]} {numbers[:3]}.{numbers[3:]}"
            else:
                return f"{prefix}-{letters}1 {numbers[:3]}.{numbers[3:]}"
        
        # Format 2: 2 digits + 1 letter + 5 digits (xe máy)
        # Example: 51A12345 -> 51A-123.45
        match = re.match(r'^(\d{2})([A-Z])(\d{5})$', clean)
        if match:
            prefix, letter, numbers = match.groups()
            return f"{prefix}{letter}-{numbers[:3]}.{numbers[3:]}"
        
        # Format 3: 2 digits + 1 letter + 4 digits (xe máy cũ)
        # Example: 51A1234 -> 51A-12.34
        match = re.match(r'^(\d{2})([A-Z])(\d{4})$', clean)
        if match:
            prefix, letter, numbers = match.groups()
            return f"{prefix}{letter}-{numbers[:2]}.{numbers[2:]}"
        
        # Return original if no match
        return text
    
    def detect_and_recognize(self, frame):
        """
        Phát hiện và nhận diện biển số từ frame
        Phiên bản đơn giản: xử lý toàn bộ ảnh như một biển số
        Returns: (plate_text, confidence, plate_bbox, plate_img)
        """
        # Sử dụng toàn bộ frame như ảnh biển số
        raw_text = self.extract_text_tesseract(frame)
        
        if not raw_text or not self.validate_plate_format(raw_text):
            return None, 0, None, None
        
        # Format biển số
        plate_text = self.format_plate_text(raw_text)
        
        # Giả định confidence cao nếu nhận diện được
        confidence = 0.85
        
        # Bbox là toàn bộ ảnh
        h, w = frame.shape[:2]
        bbox = (0, 0, w, h)
        
        return plate_text, confidence, bbox, frame
    
    def save_plate_image(self, plate_img, plate_text):
        """
        Lưu ảnh biển số vào thư mục uploads
        Returns: relative path to saved image
        """
        if plate_img is None:
            return None
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"plate_{plate_text}_{timestamp}.jpg"
        filepath = os.path.join(self.upload_folder, filename)
        
        # Save image
        cv2.imwrite(filepath, plate_img)
        
        # Return relative path
        return filepath.replace('\\', '/')
    
    def draw_detection(self, frame, bbox, text, confidence):
        """
        Vẽ bounding box và text lên frame
        """
        if bbox is None:
            return frame
        
        x1, y1, x2, y2 = bbox
        
        # Draw rectangle
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        
        # Draw text background
        label = f"{text} ({confidence:.2f})"
        (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        cv2.rectangle(frame, (x1, y1 - h - 10), (x1 + w, y1), (0, 255, 0), -1)
        
        # Draw text
        cv2.putText(frame, label, (x1, y1 - 5), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
        
        return frame


class CameraStream:
    def __init__(self, camera_index=0):
        """
        Khởi tạo camera stream
        """
        self.camera = cv2.VideoCapture(camera_index)
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.detector = LicensePlateDetector()
        
    def get_frame(self):
        """
        Lấy frame từ camera
        """
        success, frame = self.camera.read()
        if not success:
            return None
        return frame
    
    def generate_frames(self):
        """
        Generator để stream video
        Sử dụng cho Flask route /video_feed
        """
        while True:
            frame = self.get_frame()
            if frame is None:
                break
            
            # Detect and recognize
            plate_text, confidence, bbox, plate_img = self.detector.detect_and_recognize(frame)
            
            # Draw detection
            if plate_text:
                frame = self.detector.draw_detection(frame, bbox, plate_text, confidence)
            
            # Encode frame
            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                continue
            
            frame_bytes = buffer.tobytes()
            
            # Yield frame in multipart format
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
    
    def capture_and_recognize(self):
        """
        Chụp ảnh và nhận diện biển số
        Returns: dict with plate info
        """
        frame = self.get_frame()
        if frame is None:
            return {'success': False, 'message': 'Không thể lấy ảnh từ camera'}
        
        # Detect and recognize
        plate_text, confidence, bbox, plate_img = self.detector.detect_and_recognize(frame)
        
        if not plate_text:
            return {'success': False, 'message': 'Không phát hiện biển số'}
        
        # Save images
        plate_path = self.detector.save_plate_image(plate_img, plate_text)
        
        # Save full frame
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        full_frame_path = f"static/uploads/full_{plate_text}_{timestamp}.jpg"
        cv2.imwrite(full_frame_path, frame)
        
        return {
            'success': True,
            'plate_text': plate_text,
            'confidence': float(confidence),
            'plate_image': plate_path,
            'full_image': full_frame_path.replace('\\', '/'),
            'bbox': bbox
        }
    
    def release(self):
        """
        Giải phóng camera
        """
        if self.camera:
            self.camera.release()
    
    def __del__(self):
        self.release()


# Singleton instance
_camera_stream = None

def get_camera_stream():
    """
    Get or create camera stream instance
    """
    global _camera_stream
    if _camera_stream is None:
        _camera_stream = CameraStream()
    return _camera_stream

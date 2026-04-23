# 🔧 HƯỚNG DẪN CÀI ĐẶT - HỆ THỐNG BÃI XE NQT

## ❌ LỖI: ModuleNotFoundError: No module named 'pyodbc'

### Nguyên nhân:
Bạn chưa cài đặt các package Python cần thiết.

---

## ✅ GIẢI PHÁP (3 CÁCH)

### 🚀 CÁCH 1: Dùng file .bat (NHANH NHẤT - KHUYẾN NGHỊ)

```bash
# Chạy file này:
install_dependencies.bat

# Hoặc double-click vào file install_dependencies.bat
```

Script sẽ tự động:
1. Kiểm tra Python
2. Nâng cấp pip
3. Cài đặt tất cả packages

---

### 🚀 CÁCH 2: Dùng requirements.txt

```bash
# Mở PowerShell hoặc CMD tại thư mục dự án
cd E:\Quan_Ly_Bai_Xe

# Cài đặt tất cả packages
pip install -r requirements.txt
```

---

### 🚀 CÁCH 3: Cài từng package (NẾU CÁCH 1 & 2 LỖI)

```bash
# Mở PowerShell hoặc CMD
cd E:\Quan_Ly_Bai_Xe

# Cài từng package
pip install flask==3.1.3
pip install flask-mail==0.10.0
pip install pdfkit==1.0.0
pip install pyodbc==5.3.0
pip install openpyxl==3.1.5
pip install stripe==15.0.1
pip install requests==2.33.1
pip install "qrcode[pil]==8.2"
pip install Pillow==12.2.0
pip install opencv-python==4.13.0.90
pip install pytesseract==0.3.13
pip install ultralytics==8.4.33
pip install python-dotenv==1.2.2
```

---

## 🔍 KIỂM TRA SAU KHI CÀI

### Kiểm tra pyodbc đã cài chưa:
```bash
python -c "import pyodbc; print('pyodbc version:', pyodbc.version)"
```

**Kết quả mong đợi:**
```
pyodbc version: 5.3.0
```

### Kiểm tra tất cả packages:
```bash
pip list
```

**Tìm các packages sau:**
- flask
- flask-mail
- pdfkit
- pyodbc ✅ (Quan trọng nhất)
- openpyxl
- stripe
- requests
- qrcode
- Pillow
- opencv-python
- pytesseract
- ultralytics
- python-dotenv

---

## ⚠️ LƯU Ý QUAN TRỌNG

### 1. Về pyodbc:
- Package này cần **Microsoft ODBC Driver for SQL Server**
- Nếu cài pyodbc bị lỗi, cài driver trước:
  - Download: https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server
  - Chọn: **ODBC Driver 17 for SQL Server**

### 2. Về wkhtmltopdf (cho pdfkit):
- Cần cài **wkhtmltopdf** để xuất PDF
- Download: https://wkhtmltopdf.org/downloads.html
- Cài vào: `C:\Program Files\wkhtmltopdf\`

### 3. Về Tesseract (cho pytesseract):
- Cần cài **Tesseract OCR** để nhận diện biển số
- Download: https://github.com/UB-Mannheim/tesseract/wiki
- Cài vào: `C:\Program Files\Tesseract-OCR\`

---

## 🐛 TROUBLESHOOTING

### Lỗi: pip không được nhận diện
```bash
# Thử:
python -m pip install pyodbc

# Hoặc:
py -m pip install pyodbc
```

### Lỗi: Permission denied
```bash
# Chạy PowerShell/CMD với quyền Administrator
# Hoặc thêm --user:
pip install --user pyodbc
```

### Lỗi: Microsoft Visual C++ 14.0 is required
```bash
# Cài Visual C++ Build Tools:
# https://visualstudio.microsoft.com/visual-cpp-build-tools/
# Hoặc cài Visual Studio Community
```

### Lỗi: Cannot find ODBC Driver
```bash
# Cài ODBC Driver 17 for SQL Server:
# https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server
```

---

## ✅ SAU KHI CÀI XONG

### Bước 1: Kiểm tra
```bash
python -c "import pyodbc; print('OK')"
```

### Bước 2: Chạy app
```bash
python app.py
```

**Kết quả mong đợi:**
```
 * Running on http://0.0.0.0:5000
 * Running on http://127.0.0.1:5000
```

### Bước 3: Test
```
http://localhost:5000/admin/login
```

---

## 📞 HỖ TRỢ

Nếu vẫn gặp lỗi, cung cấp:
1. Lỗi đầy đủ khi chạy `pip install pyodbc`
2. Kết quả `python --version`
3. Kết quả `pip --version`
4. Hệ điều hành (Windows 10/11, 32bit/64bit)

---

## 🎯 TÓM TẮT

```
1. Chạy: install_dependencies.bat
2. Đợi cài đặt xong
3. Chạy: python app.py
4. Mở: http://localhost:5000
```

**Chúc bạn cài đặt thành công! 🚀**

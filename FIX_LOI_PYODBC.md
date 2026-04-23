# 🔧 FIX LỖI: ModuleNotFoundError: No module named 'pyodbc'

## ❌ LỖI BẠN GẶP PHẢI:

```
Traceback (most recent call last):
  File "E:\Quan_Ly_Bai_Xe\templates\app.py", line 43, in <module>
    import pyodbc
ModuleNotFoundError: No module named 'pyodbc'
```

---

## ✅ NGUYÊN NHÂN:

Bạn chưa cài đặt package `pyodbc` - package này cần thiết để kết nối với SQL Server.

---

## 🚀 GIẢI PHÁP (CHỌN 1 TRONG 3 CÁCH)

### 🥇 CÁCH 1: Dùng file .bat (NHANH NHẤT)

**Bước 1:** Tìm file `install_dependencies.bat` trong thư mục dự án

**Bước 2:** Double-click vào file đó

**Bước 3:** Đợi cài đặt xong (khoảng 2-5 phút)

**Bước 4:** Chạy lại `python app.py`

---

### 🥈 CÁCH 2: Dùng lệnh pip (KHUYẾN NGHỊ)

**Mở PowerShell hoặc CMD:**

```bash
# Bước 1: Chuyển đến thư mục dự án
cd E:\Quan_Ly_Bai_Xe

# Bước 2: Cài đặt tất cả packages
pip install -r requirements.txt

# Nếu lỗi, thử:
python -m pip install -r requirements.txt
```

**Đợi cài đặt xong, sau đó:**

```bash
# Bước 3: Chạy app
python app.py
```

---

### 🥉 CÁCH 3: Cài chỉ pyodbc (NẾU CÁCH 1 & 2 LỖI)

```bash
# Chỉ cài pyodbc
pip install pyodbc

# Nếu lỗi, thử:
python -m pip install pyodbc

# Hoặc với quyền user:
pip install --user pyodbc
```

---

## ⚠️ NẾU VẪN LỖI KHI CÀI PYODBC

### Lỗi: Microsoft Visual C++ 14.0 is required

**Giải pháp:**

1. Download và cài **Microsoft C++ Build Tools**:
   - Link: https://visualstudio.microsoft.com/visual-cpp-build-tools/
   - Hoặc: https://aka.ms/vs/17/release/vs_BuildTools.exe

2. Khi cài, chọn:
   - ✅ Desktop development with C++
   - ✅ MSVC v143 - VS 2022 C++ x64/x86 build tools
   - ✅ Windows 10 SDK

3. Sau khi cài xong, chạy lại:
   ```bash
   pip install pyodbc
   ```

---

### Lỗi: Cannot find ODBC Driver

**Giải pháp:**

1. Download và cài **ODBC Driver 17 for SQL Server**:
   - Link: https://go.microsoft.com/fwlink/?linkid=2249004
   - Hoặc: https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server

2. Chọn phiên bản phù hợp:
   - Windows 64-bit: `msodbcsql_17_x64.msi`
   - Windows 32-bit: `msodbcsql_17_x86.msi`

3. Cài đặt với các tùy chọn mặc định

4. Sau khi cài xong, chạy lại:
   ```bash
   pip install pyodbc
   ```

---

## ✅ KIỂM TRA SAU KHI CÀI

### Kiểm tra pyodbc đã cài chưa:

```bash
python -c "import pyodbc; print('pyodbc OK - version:', pyodbc.version)"
```

**Kết quả mong đợi:**
```
pyodbc OK - version: 5.3.0
```

### Kiểm tra ODBC Driver:

```bash
python -c "import pyodbc; print([x for x in pyodbc.drivers() if 'SQL Server' in x])"
```

**Kết quả mong đợi:**
```
['ODBC Driver 17 for SQL Server', 'SQL Server']
```

---

## 🎯 SAU KHI FIX XONG

### Bước 1: Chạy app

```bash
cd E:\Quan_Ly_Bai_Xe
python app.py
```

**Kết quả mong đợi:**
```
 * Running on http://0.0.0.0:5000
 * Running on http://127.0.0.1:5000
```

### Bước 2: Mở browser

```
http://localhost:5000/admin/login
```

### Bước 3: Đăng nhập

```
Email: admin@nqt.com
Password: admin123
```

---

## 📋 CHECKLIST

- [ ] Đã cài pyodbc
- [ ] Đã cài ODBC Driver 17 for SQL Server
- [ ] Chạy `python -c "import pyodbc"` không lỗi
- [ ] Chạy `python app.py` thành công
- [ ] Mở được http://localhost:5000

---

## 🐛 CÁC LỖI KHÁC CÓ THỂ GẶP

### Lỗi: pip không được nhận diện

```bash
# Thử:
python -m pip --version

# Nếu vẫn lỗi, cài lại pip:
python -m ensurepip --upgrade
```

### Lỗi: Permission denied

```bash
# Chạy CMD/PowerShell với quyền Administrator
# Hoặc thêm --user:
pip install --user pyodbc
```

### Lỗi: SSL Certificate

```bash
# Thêm --trusted-host:
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org pyodbc
```

---

## 📞 HỖ TRỢ

Nếu vẫn gặp lỗi, cung cấp:

1. **Lỗi đầy đủ** khi chạy `pip install pyodbc`
2. **Python version**: `python --version`
3. **Pip version**: `pip --version`
4. **Hệ điều hành**: Windows 10/11, 32bit/64bit
5. **Screenshot** lỗi

---

## 🎉 TÓM TẮT

```
1. Chạy: install_dependencies.bat
   HOẶC
   pip install -r requirements.txt

2. Nếu lỗi, cài:
   - Microsoft C++ Build Tools
   - ODBC Driver 17 for SQL Server

3. Chạy lại: pip install pyodbc

4. Test: python app.py

5. Mở: http://localhost:5000
```

---

**Chúc bạn fix lỗi thành công! 🚀**

Sau khi fix xong, quay lại test Giai đoạn 1 theo hướng dẫn trong `START_HERE.md`

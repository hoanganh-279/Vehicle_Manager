# 🚀 HƯỚNG DẪN DEPLOY LÊN RENDER - DUAL-MODE

## 📋 MỤC LỤC

1. [Tổng quan](#tổng-quan)
2. [Chuẩn bị trước khi deploy](#chuẩn-bị-trước-khi-deploy)
3. [Bước 1: Tạo tài khoản Render](#bước-1-tạo-tài-khoản-render)
4. [Bước 2: Push code lên GitHub](#bước-2-push-code-lên-github)
5. [Bước 3: Tạo PostgreSQL Database](#bước-3-tạo-postgresql-database)
6. [Bước 4: Chạy Schema PostgreSQL](#bước-4-chạy-schema-postgresql)
7. [Bước 5: Tạo Web Service](#bước-5-tạo-web-service)
8. [Bước 6: Cấu hình Environment Variables](#bước-6-cấu-hình-environment-variables)
9. [Bước 7: Deploy và kiểm tra](#bước-7-deploy-và-kiểm-tra)
10. [Xử lý lỗi thường gặp](#xử-lý-lỗi-thường-gặp)
11. [Rollback nếu có sự cố](#rollback-nếu-có-sự-cố)

---

## 🎯 TỔNG QUAN

### Kiến trúc Dual-Mode

```
┌─────────────────────────────────────────────────────────────┐
│                    DUAL-MODE ARCHITECTURE                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  LOCAL (Windows)              RENDER (Cloud)                │
│  ┌──────────────┐             ┌──────────────┐             │
│  │   app.py     │             │   app.py     │             │
│  │  (Flask)     │             │  (Flask)     │             │
│  └──────┬───────┘             └──────┬───────┘             │
│         │                            │                      │
│         │ db_utils.py                │ db_utils.py          │
│         │ (Auto-detect)              │ (Auto-detect)        │
│         │                            │                      │
│         ▼                            ▼                      │
│  ┌──────────────┐             ┌──────────────┐             │
│  │ SQL Server   │             │ PostgreSQL   │             │
│  │  (pyodbc)    │             │ (psycopg2)   │             │
│  └──────────────┘             └──────────────┘             │
│                                                              │
│  DATABASE_URL = None          DATABASE_URL = postgresql://  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Nguyên lý hoạt động

- **Local**: Không có `DATABASE_URL` → Dùng SQL Server (pyodbc)
- **Render**: Có `DATABASE_URL` → Dùng PostgreSQL (psycopg2)
- **db_utils.py**: Tự động nhận diện và chuyển đổi cú pháp SQL

---

## 🛠️ CHUẨN BỊ TRƯỚC KHI DEPLOY

### ✅ Checklist

- [ ] Đã test kỹ trên Local (SQL Server)
- [ ] Đã có tài khoản GitHub
- [ ] Đã có tài khoản Render (miễn phí)
- [ ] Đã có thông tin MoMo API (Partner Code, Access Key, Secret Key)
- [ ] Đã backup database Local

### 📦 Files cần thiết (đã tạo sẵn)

```
parking-management/
├── app.py                          # Flask app (chưa refactor)
├── db_utils.py                     # ✅ Dual-mode database utilities
├── fix_payment_webhook_dual.py     # ✅ Webhook với dual-mode
├── momo.py                         # MoMo integration (không cần sửa)
├── requirements.txt                # ✅ Đã có psycopg2-binary, gunicorn
├── schema_postgresql.sql           # ✅ PostgreSQL schema
├── render.yaml                     # ✅ Infrastructure as Code
├── .env.example                    # ✅ Environment variables template
└── .gitignore                      # Đảm bảo .env không bị commit
```

---

## 📝 BƯỚC 1: TẠO TÀI KHOẢN RENDER

### 1.1. Đăng ký tài khoản

1. Truy cập: https://render.com
2. Click **"Get Started"**
3. Đăng ký bằng GitHub (khuyến nghị) hoặc Email
4. Xác nhận email

### 1.2. Kích hoạt Free Tier

- Free tier bao gồm:
  - **Web Service**: 512 MB RAM, spin down sau 15 phút không hoạt động
  - **PostgreSQL**: 1 GB storage, hết hạn sau 90 ngày
  - **Disk**: 1 GB persistent storage

⚠️ **LƯU Ý**: Free tier đủ để test, nhưng production nên nâng cấp lên Starter ($7/tháng)

---

## 📤 BƯỚC 2: PUSH CODE LÊN GITHUB

### 2.1. Tạo repository mới

```bash
# Mở Git Bash hoặc Terminal trong thư mục dự án

# Khởi tạo Git (nếu chưa có)
git init

# Kiểm tra .gitignore đã có .env chưa
cat .gitignore | grep .env

# Nếu chưa có, thêm vào
echo ".env" >> .gitignore
echo "__pycache__/" >> .gitignore
echo "*.pyc" >> .gitignore
echo "venv/" >> .gitignore
```

### 2.2. Commit và push

```bash
# Add tất cả files
git add .

# Commit
git commit -m "Initial commit - Dual-mode support for Render"

# Tạo repo trên GitHub (https://github.com/new)
# Sau đó link remote

git remote add origin https://github.com/YOUR_USERNAME/parking-management.git

# Push lên GitHub
git branch -M main
git push -u origin main
```

### 2.3. Kiểm tra

- Truy cập GitHub repository
- Đảm bảo file `.env` **KHÔNG** có trong repo
- Kiểm tra các file mới đã được push:
  - `db_utils.py`
  - `fix_payment_webhook_dual.py`
  - `schema_postgresql.sql`
  - `render.yaml`
  - `.env.example`

---

## 🗄️ BƯỚC 3: TẠO POSTGRESQL DATABASE

### 3.1. Tạo database trên Render

1. Đăng nhập Render Dashboard: https://dashboard.render.com
2. Click **"New +"** → **"PostgreSQL"**
3. Điền thông tin:
   - **Name**: `parking-management-db`
   - **Database**: `parking_db`
   - **User**: `parking_user` (tự động tạo)
   - **Region**: **Singapore** (gần Việt Nam nhất)
   - **Plan**: **Free**
4. Click **"Create Database"**

### 3.2. Lấy thông tin kết nối

Sau khi tạo xong, vào tab **"Info"**:

```
Internal Database URL: postgresql://parking_user:xxxxx@dpg-xxxxx-a/parking_db
External Database URL: postgresql://parking_user:xxxxx@dpg-xxxxx-a.singapore-postgres.render.com/parking_db
```

⚠️ **LƯU Ý**: 
- **Internal URL**: Dùng cho Web Service trên Render (nhanh hơn, miễn phí bandwidth)
- **External URL**: Dùng để kết nối từ máy local (có giới hạn bandwidth)

---

## 🏗️ BƯỚC 4: CHẠY SCHEMA POSTGRESQL

### 4.1. Cài đặt PostgreSQL Client (Local)

**Windows:**
```bash
# Download PostgreSQL từ: https://www.postgresql.org/download/windows/
# Hoặc dùng Chocolatey:
choco install postgresql
```

**Hoặc dùng Render Shell (khuyến nghị):**

### 4.2. Kết nối và chạy schema

**Cách 1: Dùng Render Shell (Dễ nhất)**

1. Vào Render Dashboard → Database → **"Connect"**
2. Click **"PSQL Command"**
3. Copy lệnh, ví dụ:
   ```bash
   PGPASSWORD=xxxxx psql -h dpg-xxxxx-a.singapore-postgres.render.com -U parking_user parking_db
   ```
4. Paste vào Terminal local và chạy
5. Sau khi kết nối thành công, copy toàn bộ nội dung file `schema_postgresql.sql`
6. Paste vào psql và Enter

**Cách 2: Dùng file SQL**

```bash
# Kết nối và chạy file
PGPASSWORD=xxxxx psql -h dpg-xxxxx-a.singapore-postgres.render.com -U parking_user parking_db < schema_postgresql.sql
```

### 4.3. Kiểm tra tables đã tạo

```sql
-- Trong psql
\dt

-- Kết quả mong đợi:
--  Schema |       Name        | Type  |    Owner     
-- --------+-------------------+-------+--------------
--  public | balance_history   | table | parking_user
--  public | cards             | table | parking_user
--  public | parking_config    | table | parking_user
--  public | pricing_rules     | table | parking_user
--  public | topup_transactions| table | parking_user
--  public | users             | table | parking_user
--  public | vehicles          | table | parking_user

-- Kiểm tra dữ liệu mẫu
SELECT * FROM parking_config;
SELECT * FROM users;

-- Thoát
\q
```

---

## 🌐 BƯỚC 5: TẠO WEB SERVICE

### 5.1. Tạo Web Service

1. Render Dashboard → **"New +"** → **"Web Service"**
2. Chọn **"Build and deploy from a Git repository"**
3. Click **"Connect"** repository GitHub của bạn
4. Chọn repo `parking-management`

### 5.2. Cấu hình Web Service

**Basic Settings:**
- **Name**: `parking-management-app`
- **Region**: **Singapore**
- **Branch**: `main`
- **Root Directory**: (để trống)
- **Runtime**: **Python 3**
- **Build Command**:
  ```bash
  pip install --upgrade pip && pip install -r requirements.txt
  ```
- **Start Command**:
  ```bash
  gunicorn --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120 --access-logfile - --error-logfile - app:app
  ```

**Advanced Settings:**
- **Plan**: **Free**
- **Auto-Deploy**: **Yes** (tự động deploy khi push code mới)

### 5.3. Thêm Persistent Disk (cho uploads)

1. Scroll xuống **"Disk"**
2. Click **"Add Disk"**
3. Cấu hình:
   - **Name**: `parking-uploads`
   - **Mount Path**: `/opt/render/project/src/static/uploads`
   - **Size**: **1 GB**

---

## 🔐 BƯỚC 6: CẤU HÌNH ENVIRONMENT VARIABLES

### 6.1. Thêm Environment Variables

Vào tab **"Environment"** của Web Service, thêm các biến sau:

#### Database (Tự động)
```
DATABASE_URL = [Link to parking-management-db]
```
👉 Click **"Add from Database"** → Chọn `parking-management-db`

#### Flask
```
FLASK_ENV = production
SECRET_KEY = [Auto-generate] (Click "Generate")
```

#### Timezone
```
TZ = Asia/Ho_Chi_Minh
```

#### MoMo Payment
```
MOMO_ENDPOINT = https://test-payment.momo.vn/v2/gateway/api/create
MOMO_PARTNER_CODE = [Lấy từ MoMo Partner Portal]
MOMO_ACCESS_KEY = [Lấy từ MoMo Partner Portal]
MOMO_SECRET_KEY = [Lấy từ MoMo Partner Portal]
```

#### MoMo Callback URLs
```
MOMO_REDIRECT_URL = https://parking-management-app.onrender.com/payment/result
MOMO_IPN_URL = https://parking-management-app.onrender.com/payment/result
```

⚠️ **QUAN TRỌNG**: Thay `parking-management-app` bằng tên app thực tế của bạn!

#### Gunicorn (Optional)
```
GUNICORN_WORKERS = 2
GUNICORN_THREADS = 4
GUNICORN_TIMEOUT = 120
```

### 6.2. Lưu và Deploy

Click **"Save Changes"** → Render sẽ tự động deploy

---

## 🚀 BƯỚC 7: DEPLOY VÀ KIỂM TRA

### 7.1. Theo dõi quá trình deploy

1. Vào tab **"Logs"** của Web Service
2. Xem real-time logs:
   ```
   ==> Cloning from https://github.com/...
   ==> Running build command: pip install...
   ==> Build successful
   ==> Starting service with: gunicorn...
   ==> Your service is live 🎉
   ```

### 7.2. Kiểm tra app đã chạy

Truy cập URL: `https://parking-management-app.onrender.com`

**Kết quả mong đợi:**
- Trang chủ hiển thị bình thường
- Không có lỗi 500
- Database kết nối thành công

### 7.3. Test các chức năng chính

#### Test 1: Đăng nhập Admin
```
URL: https://parking-management-app.onrender.com/admin/login
Username: admin
Password: admin123
```

#### Test 2: Xem Dashboard
```
URL: https://parking-management-app.onrender.com/admin/dashboard
```

#### Test 3: Đăng ký thẻ mới
```
URL: https://parking-management-app.onrender.com/card/register
```

#### Test 4: Nạp tiền (MoMo)
```
URL: https://parking-management-app.onrender.com/card/topup
- Nhập card_id
- Nhập số tiền
- Click "Nạp tiền"
- Kiểm tra redirect đến MoMo
```

### 7.4. Kiểm tra logs

```bash
# Xem logs real-time
# Vào Render Dashboard → Logs

# Hoặc dùng Render CLI
render logs -s parking-management-app --tail
```

---

## ⚠️ XỬ LÝ LỖI THƯỜNG GẶP

### Lỗi 1: ModuleNotFoundError: No module named 'psycopg2'

**Nguyên nhân**: `requirements.txt` thiếu `psycopg2-binary`

**Giải pháp**:
```bash
# Thêm vào requirements.txt
echo "psycopg2-binary==2.9.9" >> requirements.txt

# Commit và push
git add requirements.txt
git commit -m "Add psycopg2-binary"
git push
```

### Lỗi 2: OperationalError: could not connect to server

**Nguyên nhân**: `DATABASE_URL` sai hoặc database chưa sẵn sàng

**Giải pháp**:
1. Kiểm tra database đã chạy: Render Dashboard → Database → Status = "Available"
2. Kiểm tra `DATABASE_URL` trong Environment Variables
3. Restart Web Service

### Lỗi 3: Application failed to respond

**Nguyên nhân**: Gunicorn timeout hoặc app crash khi start

**Giải pháp**:
```bash
# Kiểm tra logs
# Tìm dòng lỗi đầu tiên

# Thường do:
# - Import error
# - Database connection error
# - Missing environment variable

# Fix và push lại
```

### Lỗi 4: 502 Bad Gateway

**Nguyên nhân**: App không bind đúng port

**Giải pháp**:
```bash
# Đảm bảo Start Command có $PORT
gunicorn --bind 0.0.0.0:$PORT app:app

# Không được hard-code port 5000!
```

### Lỗi 5: Free tier spin down (App ngủ)

**Hiện tượng**: Lần đầu truy cập sau 15 phút chờ lâu (30-60s)

**Giải pháp**:
- **Tạm thời**: Chấp nhận (free tier)
- **Lâu dài**: Nâng cấp lên Starter plan ($7/tháng)
- **Workaround**: Dùng cron job ping app mỗi 10 phút (https://cron-job.org)

### Lỗi 6: MoMo callback không hoạt động

**Nguyên nhân**: IPN URL chưa cập nhật

**Giải pháp**:
1. Vào MoMo Partner Portal
2. Cập nhật IPN URL: `https://parking-management-app.onrender.com/payment/result`
3. Test lại webhook

---

## 🔄 ROLLBACK NẾU CÓ SỰ CỐ

### Kịch bản: Deploy lên Render bị lỗi nghiêm trọng

### Bước 1: Rollback code trên Render

1. Render Dashboard → Web Service → **"Manual Deploy"**
2. Chọn commit trước đó (commit hash)
3. Click **"Deploy"**

### Bước 2: Rollback database (nếu cần)

```bash
# Kết nối PostgreSQL
PGPASSWORD=xxxxx psql -h dpg-xxxxx-a.singapore-postgres.render.com -U parking_user parking_db

# Rollback schema (nếu có migration)
# Hoặc restore từ backup
```

### Bước 3: Kiểm tra Local vẫn hoạt động

```bash
# Local vẫn dùng SQL Server, không bị ảnh hưởng
python app.py
```

### Bước 4: Fix lỗi và deploy lại

```bash
# Fix code
# Test kỹ trên local
# Commit và push
git add .
git commit -m "Fix deployment issue"
git push
```

---

## 📊 MONITORING VÀ MAINTENANCE

### 1. Xem Metrics

Render Dashboard → Web Service → **"Metrics"**
- CPU Usage
- Memory Usage
- Request Count
- Response Time

### 2. Xem Logs

```bash
# Real-time logs
Render Dashboard → Logs

# Hoặc dùng CLI
render logs -s parking-management-app --tail
```

### 3. Backup Database

```bash
# Export PostgreSQL
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# Hoặc dùng Render Dashboard → Database → Backups
```

### 4. Scale Up (Nếu cần)

Render Dashboard → Web Service → **"Settings"** → **"Plan"**
- Nâng cấp lên **Starter** ($7/tháng): 512 MB RAM, không spin down
- Nâng cấp lên **Standard** ($25/tháng): 2 GB RAM, auto-scaling

---

## ✅ CHECKLIST HOÀN THÀNH

- [ ] Database PostgreSQL đã tạo và chạy schema
- [ ] Web Service đã deploy thành công
- [ ] Environment Variables đã cấu hình đầy đủ
- [ ] App truy cập được qua HTTPS
- [ ] Đăng nhập admin thành công
- [ ] Dashboard hiển thị dữ liệu
- [ ] MoMo callback hoạt động (test nạp tiền)
- [ ] Local vẫn chạy bình thường với SQL Server
- [ ] Đã backup database Local
- [ ] Đã cập nhật MoMo IPN URL

---

## 🎉 HOÀN THÀNH!

Hệ thống của bạn đã chạy trên Render với PostgreSQL, trong khi Local vẫn dùng SQL Server!

**Next Steps:**
1. Test kỹ tất cả chức năng trên Production
2. Cập nhật DNS nếu có custom domain
3. Thiết lập monitoring và alerting
4. Backup database định kỳ
5. Nâng cấp lên paid plan khi cần

**Hỗ trợ:**
- Render Docs: https://render.com/docs
- PostgreSQL Docs: https://www.postgresql.org/docs/
- GitHub Issues: [Link to your repo]

---

**Tác giả**: KIRO AI Assistant  
**Ngày tạo**: 2026-04-21  
**Phiên bản**: 1.0.0

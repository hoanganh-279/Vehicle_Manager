# ✅ CHECKLIST DEPLOY RENDER - DUAL-MODE

## 📋 TỔNG QUAN

Checklist đầy đủ để deploy Parking Management System lên Render với dual-mode support (PostgreSQL + SQL Server).

---

## 🎯 PHASE 1: CHUẨN BỊ

### 1.1. Kiểm tra môi trường Local
- [ ] App chạy ổn định trên Local (SQL Server)
- [ ] Tất cả chức năng hoạt động bình thường
- [ ] Không có lỗi trong logs
- [ ] Database có đầy đủ dữ liệu test

### 1.2. Backup dữ liệu
- [ ] Backup database SQL Server
- [ ] Backup source code (git commit)
- [ ] Lưu file `.env` vào nơi an toàn (không commit)

### 1.3. Tài khoản và credentials
- [ ] Có tài khoản GitHub
- [ ] Có tài khoản Render (https://render.com)
- [ ] Có thông tin MoMo API:
  - [ ] MOMO_PARTNER_CODE
  - [ ] MOMO_ACCESS_KEY
  - [ ] MOMO_SECRET_KEY

### 1.4. Đọc tài liệu
- [ ] Đọc `QUICK_START_RENDER.txt`
- [ ] Đọc `HUONG_DAN_DEPLOY_RENDER.md`
- [ ] Đọc `MIGRATION_GUIDE_APP_PY.md`
- [ ] Đọc `ARCHITECTURE_DIAGRAM.txt`

---

## 🔧 PHASE 2: REFACTOR CODE

### 2.1. Backup app.py
```bash
cp app.py app.py.backup
```
- [ ] File `app.py.backup` đã tạo

### 2.2. Refactor imports (Dòng 1-20)
- [ ] Import `db_utils` functions
- [ ] Import `fix_payment_webhook_dual`
- [ ] Xóa `import pyodbc` (nếu không dùng trực tiếp)

### 2.3. Xóa hàm cũ
- [ ] Xóa hàm `get_db()` cũ (dòng ~50-70)
- [ ] Xóa hàm `query_db()` cũ (dòng ~80-100)
- [ ] Xóa hàm `execute_db()` cũ (dòng ~110-130)

### 2.4. Refactor queries - TOP N (≈15 chỗ)
- [ ] Admin dashboard: `SELECT TOP 1 * FROM parking_config`
- [ ] Recent vehicles: `SELECT TOP 10 * FROM vehicles`
- [ ] Revenue reports: `SELECT TOP 100 * FROM vehicles`
- [ ] Tất cả queries khác có `TOP N`

**Pattern:**
```python
# Before
query = "SELECT TOP 10 * FROM vehicles"

# After
query = f"SELECT {sql_limit(10)} * FROM vehicles {sql_limit_clause(10)}"
```

### 2.5. Refactor queries - GETDATE() (≈20 chỗ)
- [ ] Insert vehicles: `entry_time = GETDATE()`
- [ ] Update exit: `exit_time = GETDATE()`
- [ ] Topup transactions: `created_at = GETDATE()`
- [ ] Balance history: `created_at = GETDATE()`
- [ ] Tất cả queries khác có `GETDATE()`

**Pattern:**
```python
# Before
query = "UPDATE vehicles SET exit_time = GETDATE() WHERE id = ?"

# After
query = f"UPDATE vehicles SET exit_time = {sql_now()} WHERE id = {'%s' if IS_POSTGRESQL else '?'}"
```

### 2.6. Refactor queries - Row Locking (≈5 chỗ)
- [ ] Parking exit: Lock vehicle row
- [ ] Card topup: Lock card row
- [ ] Webhook: Lock transaction rows

**Pattern:**
```python
# Before
query = "SELECT * FROM vehicles WITH (UPDLOCK, ROWLOCK) WHERE id = ?"

# After
query = f"SELECT * FROM vehicles {sql_lock_row()} WHERE id = {'%s' if IS_POSTGRESQL else '?'}"
```

### 2.7. Refactor queries - ISNULL() (≈8 chỗ)
- [ ] Balance checks: `ISNULL(balance, 0)`
- [ ] Count queries: `ISNULL(COUNT(*), 0)`

**Pattern:**
```python
# Before
query = "SELECT ISNULL(balance, 0) FROM cards WHERE id = ?"

# After
query = f"SELECT {sql_isnull('balance', 0)} FROM cards WHERE id = {'%s' if IS_POSTGRESQL else '?'}"
```

### 2.8. Refactor placeholders (TẤT CẢ queries)
- [ ] Tất cả `?` → Conditional `%s` hoặc `?`

**Pattern:**
```python
# Before
cursor.execute("SELECT * FROM vehicles WHERE id = ?", [vehicle_id])

# After
cursor.execute(f"SELECT * FROM vehicles WHERE id = {'%s' if IS_POSTGRESQL else '?'}", [vehicle_id])
```

### 2.9. Thêm initialization (Cuối file)
- [ ] Thêm `@app.before_first_request` với `init_db()`
- [ ] Thêm `@app.teardown_appcontext`
- [ ] Thêm `atexit.register(close_db)`

### 2.10. Update webhook import
- [ ] Thay `from fix_payment_webhook import` → `from fix_payment_webhook_dual import`

---

## 🧪 PHASE 3: TESTING LOCAL

### 3.1. Test app.py refactored
```bash
python app.py
```
- [ ] App khởi động không lỗi
- [ ] Logs hiển thị: `🗄️  Using SQL Server (Local)`
- [ ] Truy cập http://localhost:5000 thành công

### 3.2. Test các chức năng chính
- [ ] Đăng nhập admin: `/admin/login`
- [ ] Xem dashboard: `/admin/dashboard`
- [ ] Đăng ký thẻ: `/card/register`
- [ ] Nạp tiền: `/card/topup`
- [ ] Xe vào bãi: `/parking/entry`
- [ ] Xe ra bãi: `/parking/exit`
- [ ] Thanh toán MoMo: Test payment flow

### 3.3. Kiểm tra logs
- [ ] Không có lỗi trong console
- [ ] Database queries execute thành công
- [ ] Không có warning về syntax

---

## 📤 PHASE 4: PUSH CODE LÊN GITHUB

### 4.1. Kiểm tra .gitignore
```bash
cat .gitignore | grep .env
```
- [ ] File `.env` có trong `.gitignore`
- [ ] File `__pycache__/` có trong `.gitignore`
- [ ] File `venv/` có trong `.gitignore`

### 4.2. Git commit
```bash
git add .
git commit -m "Add dual-mode support for Render deployment"
```
- [ ] Commit thành công
- [ ] Kiểm tra `git status` (clean)

### 4.3. Tạo GitHub repository
- [ ] Truy cập https://github.com/new
- [ ] Tạo repo mới: `parking-management`
- [ ] Visibility: Private (khuyến nghị)

### 4.4. Push code
```bash
git remote add origin https://github.com/YOUR_USERNAME/parking-management.git
git branch -M main
git push -u origin main
```
- [ ] Push thành công
- [ ] Kiểm tra code trên GitHub
- [ ] Đảm bảo `.env` KHÔNG có trong repo

---

## 🗄️ PHASE 5: TẠO POSTGRESQL DATABASE

### 5.1. Đăng nhập Render
- [ ] Truy cập https://dashboard.render.com
- [ ] Đăng nhập bằng GitHub

### 5.2. Tạo PostgreSQL Database
- [ ] Click **"New +"** → **"PostgreSQL"**
- [ ] Name: `parking-management-db`
- [ ] Database: `parking_db`
- [ ] User: `parking_user` (auto)
- [ ] Region: **Singapore**
- [ ] Plan: **Free**
- [ ] Click **"Create Database"**

### 5.3. Chờ database khởi tạo
- [ ] Status: **Creating** → **Available** (1-2 phút)
- [ ] Lấy connection string từ tab **"Info"**

### 5.4. Lưu connection info
```
Internal Database URL: postgresql://parking_user:xxxxx@dpg-xxxxx-a/parking_db
External Database URL: postgresql://parking_user:xxxxx@dpg-xxxxx-a.singapore-postgres.render.com/parking_db
```
- [ ] Copy Internal URL (dùng cho Web Service)
- [ ] Copy External URL (dùng để chạy schema)

---

## 🏗️ PHASE 6: CHẠY SCHEMA POSTGRESQL

### 6.1. Cài đặt PostgreSQL Client (nếu chưa có)
**Windows:**
```bash
# Download từ: https://www.postgresql.org/download/windows/
# Hoặc dùng Chocolatey:
choco install postgresql
```
- [ ] PostgreSQL client đã cài đặt
- [ ] Command `psql` hoạt động

### 6.2. Kết nối database
```bash
PGPASSWORD=xxxxx psql -h dpg-xxxxx-a.singapore-postgres.render.com -U parking_user parking_db
```
- [ ] Kết nối thành công
- [ ] Prompt hiển thị: `parking_db=>`

### 6.3. Chạy schema
**Cách 1: Copy/Paste**
- [ ] Mở file `schema_postgresql.sql`
- [ ] Copy toàn bộ nội dung
- [ ] Paste vào psql
- [ ] Enter

**Cách 2: Chạy file**
```bash
PGPASSWORD=xxxxx psql -h dpg-xxxxx-a.singapore-postgres.render.com -U parking_user parking_db < schema_postgresql.sql
```
- [ ] Schema chạy thành công
- [ ] Không có lỗi

### 6.4. Kiểm tra tables
```sql
\dt
```
- [ ] 7 tables đã tạo:
  - [ ] users
  - [ ] parking_config
  - [ ] pricing_rules
  - [ ] cards
  - [ ] vehicles
  - [ ] topup_transactions
  - [ ] balance_history

### 6.5. Kiểm tra dữ liệu mẫu
```sql
SELECT * FROM parking_config;
SELECT * FROM users;
```
- [ ] parking_config có 1 row
- [ ] users có 1 row (admin)

### 6.6. Thoát psql
```sql
\q
```

---

## 🌐 PHASE 7: TẠO WEB SERVICE

### 7.1. Tạo Web Service
- [ ] Render Dashboard → **"New +"** → **"Web Service"**
- [ ] Chọn **"Build and deploy from a Git repository"**
- [ ] Click **"Connect"** GitHub repository
- [ ] Chọn repo: `parking-management`

### 7.2. Cấu hình Basic Settings
- [ ] **Name**: `parking-management-app`
- [ ] **Region**: **Singapore**
- [ ] **Branch**: `main`
- [ ] **Root Directory**: (để trống)
- [ ] **Runtime**: **Python 3**

### 7.3. Cấu hình Build Command
```bash
pip install --upgrade pip && pip install -r requirements.txt
```
- [ ] Build Command đã nhập

### 7.4. Cấu hình Start Command
```bash
gunicorn --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120 --access-logfile - --error-logfile - app:app
```
- [ ] Start Command đã nhập
- [ ] Có `$PORT` (không hard-code 5000!)

### 7.5. Cấu hình Advanced Settings
- [ ] **Plan**: **Free**
- [ ] **Auto-Deploy**: **Yes**

### 7.6. Thêm Persistent Disk
- [ ] Click **"Add Disk"**
- [ ] **Name**: `parking-uploads`
- [ ] **Mount Path**: `/opt/render/project/src/static/uploads`
- [ ] **Size**: **1 GB**

### 7.7. Tạo Web Service
- [ ] Click **"Create Web Service"**
- [ ] Chờ khởi tạo (2-3 phút)

---

## 🔐 PHASE 8: CẤU HÌNH ENVIRONMENT VARIABLES

### 8.1. Vào tab Environment
- [ ] Web Service → Tab **"Environment"**

### 8.2. Thêm DATABASE_URL
- [ ] Click **"Add Environment Variable"**
- [ ] Chọn **"Add from Database"**
- [ ] Chọn database: `parking-management-db`
- [ ] Key: `DATABASE_URL` (auto)
- [ ] Value: `postgresql://...` (auto)

### 8.3. Thêm Flask settings
- [ ] `FLASK_ENV` = `production`
- [ ] `SECRET_KEY` = [Click "Generate"]

### 8.4. Thêm Timezone
- [ ] `TZ` = `Asia/Ho_Chi_Minh`

### 8.5. Thêm MoMo credentials
- [ ] `MOMO_ENDPOINT` = `https://test-payment.momo.vn/v2/gateway/api/create`
- [ ] `MOMO_PARTNER_CODE` = [Lấy từ MoMo Portal]
- [ ] `MOMO_ACCESS_KEY` = [Lấy từ MoMo Portal]
- [ ] `MOMO_SECRET_KEY` = [Lấy từ MoMo Portal]

### 8.6. Thêm MoMo callback URLs
⚠️ **QUAN TRỌNG**: Thay `parking-management-app` bằng tên app thực tế!

- [ ] `MOMO_REDIRECT_URL` = `https://parking-management-app.onrender.com/payment/result`
- [ ] `MOMO_IPN_URL` = `https://parking-management-app.onrender.com/payment/result`

### 8.7. Lưu changes
- [ ] Click **"Save Changes"**
- [ ] Render tự động deploy lại

---

## 🚀 PHASE 9: DEPLOY VÀ KIỂM TRA

### 9.1. Theo dõi deployment
- [ ] Tab **"Logs"** → Xem real-time logs
- [ ] Chờ build hoàn thành (3-5 phút)

### 9.2. Kiểm tra logs
```
==> Cloning from https://github.com/...
==> Running build command: pip install...
==> Build successful
==> Starting service with: gunicorn...
==> Your service is live 🎉
```
- [ ] Build thành công
- [ ] Logs hiển thị: `🐘 Using PostgreSQL (Render)`
- [ ] Không có lỗi

### 9.3. Truy cập app
- [ ] URL: `https://parking-management-app.onrender.com`
- [ ] Trang chủ hiển thị bình thường
- [ ] Không có lỗi 500

### 9.4. Test đăng nhập admin
- [ ] URL: `/admin/login`
- [ ] Username: `admin`
- [ ] Password: `admin123`
- [ ] Đăng nhập thành công

### 9.5. Test dashboard
- [ ] URL: `/admin/dashboard`
- [ ] Dashboard hiển thị dữ liệu
- [ ] Charts render đúng
- [ ] Không có lỗi

### 9.6. Test các chức năng
- [ ] Đăng ký thẻ: `/card/register`
- [ ] Nạp tiền: `/card/topup`
- [ ] Xe vào bãi: `/parking/entry`
- [ ] Xe ra bãi: `/parking/exit`

### 9.7. Test MoMo payment
- [ ] Tạo topup transaction
- [ ] Redirect đến MoMo
- [ ] Thanh toán test
- [ ] Callback về app
- [ ] Số dư cập nhật đúng

---

## 🔧 PHASE 10: CẤU HÌNH MOMO PORTAL

### 10.1. Đăng nhập MoMo Partner Portal
- [ ] Truy cập MoMo Partner Portal
- [ ] Đăng nhập với tài khoản partner

### 10.2. Cập nhật IPN URL
- [ ] Vào **Settings** → **Webhook**
- [ ] IPN URL: `https://parking-management-app.onrender.com/payment/result`
- [ ] Lưu thay đổi

### 10.3. Test webhook
- [ ] Tạo test payment
- [ ] Kiểm tra MoMo gửi callback
- [ ] Kiểm tra app nhận callback
- [ ] Kiểm tra logs: `[MoMo Callback] Received: ...`

---

## ✅ PHASE 11: VALIDATION

### 11.1. Kiểm tra Local vẫn hoạt động
```bash
# Local
python app.py
```
- [ ] App chạy bình thường
- [ ] Logs: `🗄️  Using SQL Server (Local)`
- [ ] Tất cả chức năng hoạt động

### 11.2. Kiểm tra Render hoạt động
- [ ] App accessible qua HTTPS
- [ ] Logs: `🐘 Using PostgreSQL (Render)`
- [ ] Tất cả chức năng hoạt động

### 11.3. Kiểm tra dual-mode
- [ ] Local dùng SQL Server ✅
- [ ] Render dùng PostgreSQL ✅
- [ ] Không conflict ✅

---

## 📊 PHASE 12: MONITORING

### 12.1. Xem Metrics
- [ ] Render Dashboard → **"Metrics"**
- [ ] CPU Usage
- [ ] Memory Usage
- [ ] Request Count
- [ ] Response Time

### 12.2. Xem Logs
- [ ] Tab **"Logs"**
- [ ] Real-time logs
- [ ] Không có lỗi

### 12.3. Health Check
- [ ] Render tự động ping app
- [ ] Health check pass

---

## 💾 PHASE 13: BACKUP

### 13.1. Backup Local Database
```bash
# SQL Server backup
# Dùng SQL Server Management Studio
```
- [ ] Backup file đã tạo
- [ ] Lưu vào nơi an toàn

### 13.2. Backup Render Database
```bash
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql
```
- [ ] Backup file đã tạo
- [ ] Lưu vào nơi an toàn

### 13.3. Backup code
```bash
git tag v1.0.0
git push --tags
```
- [ ] Tag đã tạo
- [ ] Push lên GitHub

---

## 🎉 HOÀN THÀNH!

### Checklist tổng kết
- [ ] Local chạy với SQL Server
- [ ] Render chạy với PostgreSQL
- [ ] Dual-mode hoạt động
- [ ] Tất cả chức năng test pass
- [ ] MoMo webhook hoạt động
- [ ] Monitoring setup
- [ ] Backup đã tạo

### Next Steps
- [ ] Cập nhật DNS (nếu có custom domain)
- [ ] Thiết lập alerting
- [ ] Backup định kỳ
- [ ] Nâng cấp lên paid plan (khi cần)
- [ ] Scale up (khi traffic tăng)

---

## 📚 TÀI LIỆU THAM KHẢO

- [QUICK_START_RENDER.txt](./QUICK_START_RENDER.txt)
- [HUONG_DAN_DEPLOY_RENDER.md](./HUONG_DAN_DEPLOY_RENDER.md)
- [MIGRATION_GUIDE_APP_PY.md](./MIGRATION_GUIDE_APP_PY.md)
- [ARCHITECTURE_DIAGRAM.txt](./ARCHITECTURE_DIAGRAM.txt)
- [SUMMARY_RENDER_DEPLOYMENT.md](./SUMMARY_RENDER_DEPLOYMENT.md)

---

**Tác giả**: KIRO AI Assistant  
**Ngày tạo**: 2026-04-21  
**Phiên bản**: 1.0.0

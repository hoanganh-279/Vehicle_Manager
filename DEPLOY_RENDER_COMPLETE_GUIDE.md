# 🚀 HƯỚNG DẪN DEPLOY LÊN RENDER - HOÀN CHỈNH

## 📋 YÊU CẦU

- ✅ Tài khoản GitHub
- ✅ Tài khoản Render (https://render.com)
- ✅ Database URL đã có: `postgresql://parking_management_db_cdyg_user:Z6D0MV23pMeNuwHYjDlgzpSqHAx95Dtp@dpg-d7jloll7vvec7390q6jg-a/parking_management_db_cdyg`

---

## 🔧 BƯỚC 1: CẬP NHẬT APP.PY

### 1.1. Thay thế phần imports và database config

Tìm đoạn code cũ (dòng ~50-80):
```python
import pyodbc
# ... old imports

DB_SERVER = os.getenv('DB_SERVER', ...)
def get_db():
    conn = pyodbc.connect(...)
```

**Thay bằng**:
```python
# Import database utilities
from database import (
    init_connection_pool,
    create_tables,
    get_db_connection,
    get_db_cursor,
    query_db,
    execute_db,
    close_connection_pool
)
```

### 1.2. Thêm hàm khởi tạo database

Thêm sau phần khởi tạo Flask app (dòng ~150):

```python
# =============================================================================
# DATABASE INITIALIZATION
# =============================================================================

def initialize_database():
    """Initialize database connection and create tables"""
    try:
        # Initialize connection pool
        init_connection_pool()
        app.logger.info("✅ Connection pool initialized")
        
        # Create tables if not exist
        create_tables()
        app.logger.info("✅ Database tables created")
        
        return True
    except Exception as e:
        app.logger.error(f"❌ Database initialization failed: {e}")
        return False

# Initialize database when app starts
with app.app_context():
    initialize_database()
```

### 1.3. Cập nhật hàm query_db và execute_db

**XÓA** các hàm cũ `query_db()` và `execute_db()` (nếu có)

**SỬ DỤNG** từ `database.py`:
```python
# Đã import ở trên, không cần định nghĩa lại
```

### 1.4. Cập nhật port cho Render

Tìm dòng cuối cùng (dòng ~2150):
```python
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
```

**Thay bằng**:
```python
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
```

---

## 🔧 BƯỚC 2: FIX CÁC CHỨC NĂNG QUAN TRỌNG

### 2.1. Chức năng Tạo Thẻ Thành Viên

Tìm route `/card/register` (dòng ~1900):

```python
@app.route('/card/register', methods=['GET', 'POST'])
def card_register():
    if request.method == 'POST':
        try:
            # Lấy dữ liệu từ form
            card_number = request.form.get('card_number', '').strip()
            owner_name = request.form.get('owner_name', '').strip()
            phone = request.form.get('phone', '').strip()
            email = request.form.get('email', '').strip()
            
            # Validate
            if not card_number or not owner_name:
                flash('Vui lòng nhập đầy đủ thông tin!', 'error')
                return redirect(url_for('card_register'))
            
            # Kiểm tra trùng
            existing = query_db(
                "SELECT id FROM cards WHERE card_number = %s",
                [card_number],
                one=True
            )
            
            if existing:
                flash('Số thẻ đã tồn tại!', 'error')
                return redirect(url_for('card_register'))
            
            # Insert vào database
            card_id = execute_db(
                """INSERT INTO cards (card_number, owner_name, phone, email, balance, status)
                   VALUES (%s, %s, %s, %s, 0, 'active') RETURNING id""",
                [card_number, owner_name, phone, email]
            )
            
            flash(f'Tạo thẻ thành công! Mã thẻ: {card_number}', 'success')
            return redirect(url_for('admin_cards'))
            
        except Exception as e:
            app.logger.error(f"❌ Error creating card: {e}")
            flash('Lỗi hệ thống! Vui lòng thử lại.', 'error')
            return redirect(url_for('card_register'))
    
    return render_template('card/register.html')
```

### 2.2. Chức năng Nạp Tiền (với TRANSACTION)

Tìm route `/card/topup` (dòng ~1920):

```python
@app.route('/card/topup', methods=['GET', 'POST'])
def card_topup():
    if request.method == 'POST':
        try:
            # Lấy dữ liệu
            card_id = request.form.get('card_id')
            amount = int(request.form.get('amount', 0))
            payment_method = request.form.get('payment_method', 'cash')
            
            # Validate
            if not card_id or amount <= 0:
                flash('Thông tin không hợp lệ!', 'error')
                return redirect(url_for('card_topup'))
            
            # ✅ SỬ DỤNG TRANSACTION
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    # BEGIN TRANSACTION (auto)
                    
                    # 1. Lock card row
                    cursor.execute(
                        "SELECT id, balance FROM cards WHERE id = %s FOR UPDATE",
                        [card_id]
                    )
                    card = cursor.fetchone()
                    
                    if not card:
                        conn.rollback()
                        flash('Không tìm thấy thẻ!', 'error')
                        return redirect(url_for('card_topup'))
                    
                    old_balance = card[1] or 0
                    new_balance = old_balance + amount
                    
                    # 2. Update balance
                    cursor.execute(
                        "UPDATE cards SET balance = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                        [new_balance, card_id]
                    )
                    
                    # 3. Insert topup transaction
                    transaction_id = f"TOPUP-{card_id}-{int(datetime.now().timestamp())}"
                    cursor.execute(
                        """INSERT INTO topup_transactions 
                           (card_id, amount, payment_method, status, transaction_id, completed_at)
                           VALUES (%s, %s, %s, 'completed', %s, CURRENT_TIMESTAMP)""",
                        [card_id, amount, payment_method, transaction_id]
                    )
                    
                    # 4. Insert balance history
                    cursor.execute(
                        """INSERT INTO balance_history 
                           (card_id, amount, balance_before, balance_after, type, description, transaction_id, created_by, ip_address)
                           VALUES (%s, %s, %s, %s, 'topup', %s, %s, 'admin', %s)""",
                        [card_id, amount, old_balance, new_balance, f'Nạp tiền {payment_method}', transaction_id, request.remote_addr]
                    )
                    
                    # COMMIT TRANSACTION (auto)
                    conn.commit()
            
            flash(f'Nạp tiền thành công! Số dư mới: {new_balance:,} đ', 'success')
            return redirect(url_for('admin_cards'))
            
        except Exception as e:
            app.logger.error(f"❌ Error topup: {e}")
            flash('Lỗi hệ thống! Giao dịch đã được rollback.', 'error')
            return redirect(url_for('card_topup'))
    
    # GET - hiển thị form
    cards = query_db("SELECT * FROM cards WHERE status = 'active' ORDER BY id DESC")
    return render_template('card/topup.html', cards=cards)
```

### 2.3. Fix Logic Tính Phí Đỗ Xe (PostgreSQL)

Tìm hàm `calculate_parking_fee` (dòng ~300):

```python
def calculate_parking_fee(vehicle_id):
    """Tính phí đỗ xe (PostgreSQL compatible)"""
    try:
        vehicle = query_db(
            "SELECT * FROM vehicles WHERE id = %s AND status = 'parked'",
            [vehicle_id],
            one=True
        )
        
        if not vehicle:
            return None, None, "Không tìm thấy xe"
        
        # Tính thời gian đỗ (PostgreSQL)
        entry_time = vehicle['entry_time']
        duration_seconds = (datetime.now() - entry_time).total_seconds()
        hours = max(1, int(duration_seconds / 3600) + (1 if duration_seconds % 3600 > 0 else 0))
        
        # Lấy giá
        config = query_db("SELECT * FROM parking_config LIMIT 1", one=True)
        rate = config['car_rate'] if vehicle['vehicle_type'] == 'Xe hơi' else config['motorbike_rate']
        
        fee = hours * rate
        
        return fee, vehicle, None
        
    except Exception as e:
        app.logger.error(f"❌ Calculate fee error: {e}")
        return None, None, str(e)
```

---

## 📦 BƯỚC 3: CHUẨN BỊ FILES

### 3.1. Checklist files cần có:

- ✅ `app.py` (đã cập nhật)
- ✅ `database.py` (file mới tạo)
- ✅ `requirements_render.txt` (file mới tạo)
- ✅ `.env.render.example` (file mới tạo)
- ✅ `momo.py` (giữ nguyên)
- ✅ `templates/` (giữ nguyên)
- ✅ `static/` (giữ nguyên)

### 3.2. Tạo file `.gitignore`:

```
.env
__pycache__/
*.pyc
*.pyo
venv/
.vscode/
*.log
```

---

## 🚀 BƯỚC 4: DEPLOY LÊN RENDER

### 4.1. Push code lên GitHub

```bash
git init
git add .
git commit -m "Prepare for Render deployment with PostgreSQL"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/parking-management.git
git push -u origin main
```

### 4.2. Tạo Web Service trên Render

1. Đăng nhập https://dashboard.render.com
2. Click **"New +"** → **"Web Service"**
3. Connect GitHub repository
4. Chọn repo `parking-management`

### 4.3. Cấu hình Web Service

**Basic Settings:**
- **Name**: `parking-management-app`
- **Region**: **Singapore**
- **Branch**: `main`
- **Runtime**: **Python 3**
- **Build Command**:
  ```bash
  pip install --upgrade pip && pip install -r requirements_render.txt
  ```
- **Start Command**:
  ```bash
  gunicorn --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120 app:app
  ```

**Advanced Settings:**
- **Plan**: Free (hoặc Starter $7/tháng)
- **Auto-Deploy**: Yes

### 4.4. Thêm Environment Variables

Vào tab **"Environment"**, thêm:

```
DATABASE_URL = postgresql://parking_management_db_cdyg_user:Z6D0MV23pMeNuwHYjDlgzpSqHAx95Dtp@dpg-d7jloll7vvec7390q6jg-a/parking_management_db_cdyg

PYTHON_VERSION = 3.12.9

FLASK_SECRET_KEY = [Generate random string]

FLASK_ENV = production

TZ = Asia/Ho_Chi_Minh

MOMO_ENDPOINT = https://test-payment.momo.vn/v2/gateway/api/create
MOMO_PARTNER_CODE = [Your MoMo Partner Code]
MOMO_ACCESS_KEY = [Your MoMo Access Key]
MOMO_SECRET_KEY = [Your MoMo Secret Key]
MOMO_REDIRECT_URL = https://parking-management-app.onrender.com/payment/result
MOMO_IPN_URL = https://parking-management-app.onrender.com/payment/result
```

### 4.5. Deploy

Click **"Create Web Service"** → Render sẽ tự động:
1. Clone code từ GitHub
2. Chạy Build Command
3. Chạy Start Command
4. App sẽ live tại: `https://parking-management-app.onrender.com`

---

## ✅ BƯỚC 5: KIỂM TRA

### 5.1. Xem Logs

Vào tab **"Logs"** để xem:
```
✅ Connection pool initialized
✅ Database tables created
✅ Your service is live 🎉
```

### 5.2. Test App

1. Truy cập: `https://parking-management-app.onrender.com`
2. Đăng nhập admin: `admin` / `admin123`
3. Test các chức năng:
   - Tạo thẻ
   - Nạp tiền
   - Xe vào/ra bãi

---

## 🔧 TROUBLESHOOTING

### Lỗi: "DATABASE_URL not found"
**Solution**: Kiểm tra Environment Variables đã thêm đúng chưa

### Lỗi: "Connection refused"
**Solution**: Database URL có thể sai, kiểm tra lại

### Lỗi: "Module not found"
**Solution**: Kiểm tra `requirements_render.txt` có đầy đủ packages chưa

### App chậm lần đầu (Free tier)
**Solution**: Free tier spin down sau 15 phút không hoạt động. Nâng cấp lên Starter plan để chạy 24/7.

---

## 📊 SUMMARY

### Build Command:
```bash
pip install --upgrade pip && pip install -r requirements_render.txt
```

### Start Command:
```bash
gunicorn --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120 app:app
```

### Environment Variables (Minimum):
- `DATABASE_URL` (required)
- `PYTHON_VERSION=3.12.9` (required)
- `FLASK_SECRET_KEY` (required)
- `PORT` (auto-set by Render)

---

**Hoàn thành! App của bạn đã sẵn sàng chạy 24/7 trên Render với PostgreSQL! 🎉**

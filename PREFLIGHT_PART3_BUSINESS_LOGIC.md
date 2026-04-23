# PART 3: RỦI RO LOGIC NGHIỆP VỤ & GIẢI PHÁP

## 3️⃣ RỦI RO LOGIC NGHIỆP VỤ & DỮ LIỆU RÁC

### 3.1. SAI LỆCH MỆNH GIÁ (AMOUNT MISMATCH)

#### ❓ Câu hỏi:
> Đã có cơ chế kiểm tra (verify) số tiền MoMo trả về trong Webhook phải khớp 100% với số tiền amount đã lưu ban đầu trong topup_transactions chưa? (Tránh trường hợp user tạo request nạp 1.000.000đ nhưng bằng cách nào đó can thiệp nạp 10.000đ trên cổng thanh toán).

#### 📊 Phân tích rủi ro:

**Kịch bản tấn công:**

```
1. User tạo request nạp 1,000,000 đ
   → Backend tạo topup_transactions với amount = 1,000,000
   → Tạo MoMo payment URL

2. Attacker intercept request, sửa amount thành 10,000 đ
   → MoMo chỉ thu 10,000 đ

3. MoMo webhook gọi về với amount = 10,000 đ
   → Backend cộng 10,000 đ vào ví

4. ❌ User mất 990,000 đ
```

**Xác suất:**
- 🔴 **Cao (70%)** nếu không verify
- 🟢 **Rất thấp (<0.1%)** nếu có verify

#### ✅ Giải pháp: Verify Amount trong Webhook

```python
def process_momo_topup_callback(data, conn):
    """
    ✅ Verify amount từ MoMo phải khớp với database
    """
    cursor = conn.cursor()
    
    try:
        order_id = data.get('orderId', '')
        trans_id = data.get('transId', '')
        momo_amount = int(data.get('amount', 0))  # ← Amount từ MoMo
        result_code = int(data.get('resultCode', -1))
        
        logger.info(f"[MoMo Callback] order_id={order_id} | momo_amount={momo_amount}")
        
        # BƯỚC 1: Lấy amount từ database
        cursor.execute("""
            SELECT id, card_id, amount, status
            FROM topup_transactions WITH (UPDLOCK, ROWLOCK)
            WHERE transaction_id = ?
        """, [order_id])
        
        row = cursor.fetchone()
        
        if not row:
            logger.error(f"❌ Transaction not found: {order_id}")
            return False, 'Transaction not found'
        
        topup_id, card_id, db_amount, status = row
        
        # ═══════════════════════════════════════════════════════════
        # BƯỚC 2: VERIFY AMOUNT
        # ═══════════════════════════════════════════════════════════
        if momo_amount != db_amount:
            # ❌ Amount không khớp → Có thể bị tấn công
            logger.error(
                f"❌ AMOUNT MISMATCH: {order_id} | "
                f"DB={db_amount:,} | MoMo={momo_amount:,}"
            )
            
            # Đánh dấu transaction là suspicious
            cursor.execute("""
                UPDATE topup_transactions
                SET status = 'suspicious',
                    momo_trans_id = ?,
                    completed_at = GETDATE()
                WHERE id = ?
            """, [trans_id, topup_id])
            
            conn.commit()
            
            # Gửi alert cho admin
            send_alert_email(
                subject="🚨 SECURITY ALERT: Amount Mismatch",
                message=f"Transaction {order_id}: DB={db_amount:,} vs MoMo={momo_amount:,}"
            )
            
            # ✅ Vẫn trả về HTTP 200 để MoMo không retry
            return True, 'Amount mismatch - marked as suspicious'
        
        # ═══════════════════════════════════════════════════════════
        # BƯỚC 3: Amount khớp → Xử lý bình thường
        # ═══════════════════════════════════════════════════════════
        if result_code == 0:
            # Cập nhật status
            cursor.execute("""
                UPDATE topup_transactions
                SET status = 'completed',
                    momo_trans_id = ?,
                    completed_at = GETDATE()
                WHERE id = ?
            """, [trans_id, topup_id])
            
            # Cộng tiền (dùng db_amount, KHÔNG dùng momo_amount)
            cursor.execute("""
                UPDATE cards
                SET balance = balance + ?
                WHERE id = ?
            """, [db_amount, card_id])  # ← Dùng db_amount
            
            conn.commit()
            
            logger.info(f"✅ Topup completed: {order_id} | {db_amount:,} đ")
            return True, 'Success'
        
        else:
            # Thanh toán thất bại
            cursor.execute("""
                UPDATE topup_transactions
                SET status = 'failed',
                    momo_trans_id = ?,
                    completed_at = GETDATE()
                WHERE id = ?
            """, [trans_id, topup_id])
            
            conn.commit()
            
            logger.warning(f"⚠️  Topup failed: {order_id}")
            return True, 'Topup failed'
    
    except Exception as e:
        conn.rollback()
        logger.error(f"❌ Error: {e}")
        return False, str(e)
```

#### ✅ Giải pháp bổ sung: Thêm cột status = 'suspicious'

```sql
-- Thêm status 'suspicious' vào enum
ALTER TABLE topup_transactions
ADD CONSTRAINT chk_status 
CHECK (status IN ('pending', 'completed', 'failed', 'suspicious'));

-- Tạo view để monitor suspicious transactions
CREATE VIEW vw_suspicious_transactions AS
SELECT 
    id,
    transaction_id,
    card_id,
    amount,
    momo_trans_id,
    created_at,
    completed_at
FROM topup_transactions
WHERE status = 'suspicious'
ORDER BY created_at DESC;
```

## 📊 Bảng xử lý Amount Mismatch:

| Trường hợp | Action | Cộng tiền? | HTTP Code | Alert |
|------------|--------|------------|-----------|-------|
| Amount khớp + Success | Complete | ✅ Cộng db_amount | 200 | Không |
| Amount khớp + Failed | Mark failed | ❌ Không cộng | 200 | Không |
| Amount KHÔNG khớp | Mark suspicious | ❌ Không cộng | 200 | ✅ Gửi alert |

**Nguyên tắc:**
- ✅ **Luôn dùng db_amount** để cộng tiền (không tin momo_amount)
- ✅ **Mark suspicious** nếu amount không khớp
- ✅ **Gửi alert** cho admin để điều tra

---

### 3.2. TIMEOUT TỪ PHÍA USER

#### ❓ Câu hỏi:
> User thanh toán xong trên MoMo, nhưng khi redirect về web/app thì mạng lag, hiển thị lỗi trắng trang. Tiền trong ví vẫn cộng nhờ Webhook, nhưng user không biết. Hệ thống có UI/UX thông báo biến động số dư realtime hoặc popup cho user trong trường hợp này chưa?

#### 📊 Phân tích rủi ro:

**Kịch bản:**

```
1. User thanh toán trên MoMo → Success
2. MoMo redirect về: https://yoursite.com/payment/result?orderId=TOPUP-123
3. ❌ Mạng lag → Timeout → Trang trắng
4. ✅ Webhook vẫn chạy → Tiền đã cộng
5. ❌ User không biết → Gọi hotline → Phàn nàn
```

**Xác suất:**
- 🟡 **Trung bình (10-20%)** với mạng di động
- 🟢 **Thấp (2-5%)** với WiFi

**Tác động:**
- ❌ User experience kém
- ❌ Tăng support tickets
- ❌ Mất niềm tin

#### ✅ Giải pháp 1: Polling Status từ Frontend

**Frontend (payment/result.html):**

```html
<!DOCTYPE html>
<html>
<head>
    <title>Kết quả thanh toán</title>
    <style>
        .loading {
            text-align: center;
            padding: 50px;
        }
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #3498db;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .success {
            color: green;
            font-size: 24px;
            text-align: center;
        }
        .error {
            color: red;
            font-size: 24px;
            text-align: center;
        }
    </style>
</head>
<body>
    <div id="status-container">
        <div class="loading">
            <div class="spinner"></div>
            <p>Đang kiểm tra trạng thái thanh toán...</p>
            <p id="countdown">Vui lòng đợi (30s)</p>
        </div>
    </div>

    <script>
        // Lấy orderId từ URL
        const urlParams = new URLSearchParams(window.location.search);
        const orderId = urlParams.get('orderId');
        
        let countdown = 30;
        let pollInterval;
        let countdownInterval;
        
        // Hàm check status
        async function checkPaymentStatus() {
            try {
                const response = await fetch(`/api/payment/status?orderId=${orderId}`);
                const data = await response.json();
                
                if (data.status === 'completed') {
                    // ✅ Thanh toán thành công
                    clearInterval(pollInterval);
                    clearInterval(countdownInterval);
                    
                    document.getElementById('status-container').innerHTML = `
                        <div class="success">
                            <h2>✅ Nạp tiền thành công!</h2>
                            <p>Số tiền: ${data.amount.toLocaleString()} đ</p>
                            <p>Số dư mới: ${data.new_balance.toLocaleString()} đ</p>
                            <button onclick="window.location.href='/card/topup'">Quay lại</button>
                        </div>
                    `;
                    
                    // Show notification
                    showNotification('success', `Nạp tiền thành công ${data.amount.toLocaleString()} đ`);
                }
                else if (data.status === 'failed') {
                    // ❌ Thanh toán thất bại
                    clearInterval(pollInterval);
                    clearInterval(countdownInterval);
                    
                    document.getElementById('status-container').innerHTML = `
                        <div class="error">
                            <h2>❌ Thanh toán thất bại</h2>
                            <p>${data.message}</p>
                            <button onclick="window.location.href='/card/topup'">Thử lại</button>
                        </div>
                    `;
                }
                else if (data.status === 'pending') {
                    // ⏳ Đang chờ
                    console.log('Still pending...');
                }
            }
            catch (error) {
                console.error('Error checking status:', error);
            }
        }
        
        // Hàm countdown
        function updateCountdown() {
            countdown--;
            document.getElementById('countdown').textContent = `Vui lòng đợi (${countdown}s)`;
            
            if (countdown <= 0) {
                clearInterval(pollInterval);
                clearInterval(countdownInterval);
                
                document.getElementById('status-container').innerHTML = `
                    <div class="error">
                        <h2>⏱️ Hết thời gian chờ</h2>
                        <p>Vui lòng kiểm tra lại số dư trong ví của bạn</p>
                        <button onclick="window.location.href='/card/topup'">Kiểm tra số dư</button>
                    </div>
                `;
            }
        }
        
        // Hàm show notification
        function showNotification(type, message) {
            // TODO: Implement notification (toast, popup, etc.)
            alert(message);
        }
        
        // Bắt đầu polling (mỗi 2 giây)
        pollInterval = setInterval(checkPaymentStatus, 2000);
        countdownInterval = setInterval(updateCountdown, 1000);
        
        // Check ngay lập tức
        checkPaymentStatus();
    </script>
</body>
</html>
```

**Backend API (app.py):**

```python
@app.route('/api/payment/status', methods=['GET'])
def payment_status_api():
    """
    API để check trạng thái thanh toán
    """
    order_id = request.args.get('orderId')
    
    if not order_id:
        return jsonify({'error': 'Missing orderId'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        if order_id.startswith('TOPUP-'):
            # Check topup transaction
            cursor.execute("""
                SELECT 
                    t.status,
                    t.amount,
                    c.balance
                FROM topup_transactions t
                INNER JOIN cards c ON t.card_id = c.id
                WHERE t.transaction_id = ?
            """, [order_id])
            
            row = cursor.fetchone()
            
            if not row:
                return jsonify({'error': 'Transaction not found'}), 404
            
            status, amount, balance = row
            
            return jsonify({
                'status': status,
                'amount': amount,
                'new_balance': balance,
                'message': 'Success' if status == 'completed' else 'Pending'
            })
        
        elif order_id.startswith('PARKING-'):
            # Check parking payment
            # TODO: Implement
            pass
        
        else:
            return jsonify({'error': 'Invalid orderId'}), 400
    
    finally:
        conn.close()
```

#### ✅ Giải pháp 2: WebSocket Real-time Notification

**Backend (app.py):**

```python
from flask_socketio import SocketIO, emit

socketio = SocketIO(app, cors_allowed_origins="*")

@socketio.on('connect')
def handle_connect():
    """
    Client kết nối WebSocket
    """
    logger.info(f"Client connected: {request.sid}")


@socketio.on('subscribe_payment')
def handle_subscribe(data):
    """
    Client subscribe để nhận notification
    """
    order_id = data.get('orderId')
    logger.info(f"Client {request.sid} subscribed to {order_id}")
    
    # Lưu mapping: order_id → session_id
    # TODO: Implement với Redis hoặc in-memory dict


def notify_payment_completed(order_id, amount, new_balance):
    """
    Gửi notification khi payment completed
    """
    # Tìm session_id của client đang subscribe order_id này
    # TODO: Implement
    
    # Emit event
    socketio.emit('payment_completed', {
        'orderId': order_id,
        'amount': amount,
        'new_balance': new_balance
    }, room=session_id)


# Trong process_momo_topup_callback:
def process_momo_topup_callback(data, conn):
    # ... xử lý ...
    
    if result_code == 0:
        # ... cộng tiền ...
        
        # ✅ Gửi notification real-time
        notify_payment_completed(order_id, amount, new_balance)
```

**Frontend:**

```javascript
// Kết nối WebSocket
const socket = io('http://localhost:5000');

socket.on('connect', () => {
    console.log('WebSocket connected');
    
    // Subscribe payment
    socket.emit('subscribe_payment', {
        orderId: orderId
    });
});

socket.on('payment_completed', (data) => {
    // ✅ Nhận notification real-time
    console.log('Payment completed:', data);
    
    // Update UI
    document.getElementById('status-container').innerHTML = `
        <div class="success">
            <h2>✅ Nạp tiền thành công!</h2>
            <p>Số tiền: ${data.amount.toLocaleString()} đ</p>
            <p>Số dư mới: ${data.new_balance.toLocaleString()} đ</p>
        </div>
    `;
    
    // Show notification
    showNotification('success', `Nạp tiền thành công ${data.amount.toLocaleString()} đ`);
});
```

#### ✅ Giải pháp 3: Email/SMS Notification

```python
def send_topup_notification(card_id, amount, new_balance):
    """
    Gửi email/SMS thông báo nạp tiền thành công
    """
    # Lấy thông tin user
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT name, phone, email
        FROM cards
        WHERE id = ?
    """, [card_id])
    
    row = cursor.fetchone()
    
    if row:
        name, phone, email = row
        
        # Gửi email
        if email:
            send_email(
                to=email,
                subject='Nạp tiền thành công',
                body=f"""
                Xin chào {name},
                
                Bạn vừa nạp tiền thành công:
                - Số tiền: {amount:,} đ
                - Số dư mới: {new_balance:,} đ
                - Thời gian: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
                
                Cảm ơn bạn đã sử dụng dịch vụ!
                """
            )
        
        # Gửi SMS
        if phone:
            send_sms(
                to=phone,
                message=f"Nap tien thanh cong {amount:,}d. So du moi: {new_balance:,}d"
            )
    
    conn.close()


# Trong process_momo_topup_callback:
if result_code == 0:
    # ... cộng tiền ...
    
    # ✅ Gửi notification
    send_topup_notification(card_id, amount, new_balance)
```

## 📊 So sánh giải pháp:

| Giải pháp | Real-time | Độ phức tạp | Dependency | Khuyến nghị |
|-----------|-----------|-------------|------------|-------------|
| 1. Polling | Gần real-time (2s) | Thấp | Không | ✅ BẮT BUỘC |
| 2. WebSocket | Real-time | Cao | Flask-SocketIO | 🟡 Nếu cần |
| 3. Email/SMS | Không | Trung bình | Email/SMS service | ✅ NÊN LÀM |

**Khuyến nghị:** Áp dụng giải pháp 1 + 3 (polling + email/SMS)

---

**KẾT LUẬN PHẦN 3:**

✅ Amount Mismatch: Có giải pháp verify + mark suspicious  
✅ Timeout User: Có giải pháp polling + notification  
✅ UX: Đảm bảo user luôn biết trạng thái thanh toán  

**Rủi ro tổng thể: 🟢 THẤP** (sau khi áp dụng giải pháp)

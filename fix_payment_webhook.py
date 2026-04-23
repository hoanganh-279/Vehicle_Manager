"""
═══════════════════════════════════════════════════════════════════════════
FIX PAYMENT WEBHOOK - PRODUCTION-READY VERSION
═══════════════════════════════════════════════════════════════════════════
File này thay thế route /payment/result trong app.py
Đã fix tất cả vấn đề CRITICAL về webhook/callback
═══════════════════════════════════════════════════════════════════════════
"""

import pyodbc
import logging
from datetime import datetime
from flask import request, jsonify, render_template
from momo import verify_momo_ipn

logger = logging.getLogger(__name__)

def get_db():
    """Tạo kết nối database"""
    conn = pyodbc.connect(
        f'DRIVER={{ODBC Driver 17 for SQL Server}};'
        f'SERVER={os.getenv("DB_SERVER", r"LAPTOP-3J6T1I18\SQLEXPRESS01")};'
        f'DATABASE={os.getenv("DB_DATABASE", "ParkingManagement")};'
        f'Trusted_Connection=yes;'
    )
    conn.setdecoding(pyodbc.SQL_WCHAR, encoding='utf-16-le')
    conn.setencoding(encoding='utf-16-le')
    return conn


def process_momo_topup_callback(data, conn):
    """
    ✅ Xử lý callback nạp tiền MoMo với idempotency
    
    Args:
        data: dict từ MoMo callback
        conn: database connection
    
    Returns:
        (success: bool, message: str)
    """
    cursor = conn.cursor()
    
    try:
        order_id = data.get('orderId', '')
        trans_id = data.get('transId', '')  # ← MoMo transaction ID (unique)
        amount = int(data.get('amount', 0))
        result_code = int(data.get('resultCode', -1))
        
        logger.info(f"[MoMo Callback] order_id={order_id} | trans_id={trans_id} | result_code={result_code}")
        
        # ✅ BƯỚC 1: Kiểm tra idempotency bằng momo_trans_id
        cursor.execute("""
            SELECT id, status
            FROM topup_transactions
            WHERE momo_trans_id = ?
        """, [trans_id])
        
        existing = cursor.fetchone()
        
        if existing:
            logger.warning(f"⚠️ Duplicate MoMo callback: {trans_id} - Already processed")
            return True, 'Already processed'
        
        # ✅ BƯỚC 2: Lock row topup_transactions
        cursor.execute("""
            SELECT id, card_id, amount, status
            FROM topup_transactions WITH (UPDLOCK, ROWLOCK)
            WHERE transaction_id = ?
        """, [order_id])
        
        row = cursor.fetchone()
        
        if not row:
            logger.error(f"❌ Transaction not found: {order_id}")
            return False, 'Transaction not found'
        
        topup_id, card_id, topup_amount, status = row
        
        # Kiểm tra đã completed chưa (double check)
        if status == 'completed':
            logger.warning(f"⚠️ Transaction already completed: {order_id}")
            return True, 'Already completed'
        
        # ✅ BƯỚC 3: Xử lý theo result_code
        if result_code == 0:
            # Thanh toán thành công
            
            # 3.1. Cập nhật topup_transactions
            cursor.execute("""
                UPDATE topup_transactions
                SET status = 'completed',
                    momo_trans_id = ?,
                    completed_at = GETDATE()
                WHERE id = ?
            """, [trans_id, topup_id])
            
            # 3.2. Lock card để tránh race condition
            cursor.execute("""
                SELECT id, balance
                FROM cards WITH (UPDLOCK, ROWLOCK)
                WHERE id = ?
            """, [card_id])
            
            card_row = cursor.fetchone()
            
            if not card_row:
                logger.error(f"❌ Card not found: {card_id}")
                conn.rollback()
                return False, 'Card not found'
            
            card_balance_before = card_row[1] or 0
            
            # 3.3. Cộng tiền vào thẻ
            cursor.execute("""
                UPDATE cards
                SET balance = balance + ?
                WHERE id = ?
            """, [topup_amount, card_id])
            
            # 3.4. Ghi log vào balance_history
            cursor.execute("""
                INSERT INTO balance_history (
                    card_id, 
                    amount, 
                    balance_before,
                    balance_after,
                    type, 
                    description, 
                    transaction_id,
                    created_at,
                    created_by,
                    ip_address
                )
                VALUES (?, ?, ?, ?, 'topup', ?, ?, GETDATE(), 'MOMO_CALLBACK', ?)
            """, [
                card_id, 
                topup_amount, 
                card_balance_before,
                card_balance_before + topup_amount,
                f'Nạp tiền MoMo - {order_id}',
                order_id,
                request.remote_addr
            ])
            
            # 3.5. Commit transaction
            conn.commit()
            
            logger.info(f"✅ Topup completed: {order_id} | card_id={card_id} | amount={topup_amount:,} đ")
            
            return True, 'Topup completed successfully'
        
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
            
            logger.warning(f"⚠️ Topup failed: {order_id} | result_code={result_code}")
            
            return True, 'Topup failed'
    
    except Exception as e:
        conn.rollback()
        logger.error(f"❌ Error processing MoMo topup callback: {e}")
        return False, f'Processing error: {str(e)}'


def process_momo_parking_callback(data, conn):
    """
    ✅ Xử lý callback thanh toán phí đỗ xe MoMo
    
    Args:
        data: dict từ MoMo callback
        conn: database connection
    
    Returns:
        (success: bool, message: str)
    """
    cursor = conn.cursor()
    
    try:
        order_id = data.get('orderId', '')  # Format: PARKING-{vehicle_id}-{amount}
        trans_id = data.get('transId', '')
        amount = int(data.get('amount', 0))
        result_code = int(data.get('resultCode', -1))
        
        # Parse vehicle_id từ order_id
        parts = order_id.split('-')
        if len(parts) < 2:
            logger.error(f"❌ Invalid order_id format: {order_id}")
            return False, 'Invalid order_id format'
        
        vehicle_id = int(parts[1])
        
        logger.info(f"[MoMo Parking] vehicle_id={vehicle_id} | trans_id={trans_id} | result_code={result_code}")
        
        # ✅ BƯỚC 1: Kiểm tra idempotency
        cursor.execute("""
            SELECT id, payment_status
            FROM vehicles
            WHERE id = ? AND momo_trans_id = ?
        """, [vehicle_id, trans_id])
        
        existing = cursor.fetchone()
        
        if existing:
            logger.warning(f"⚠️ Duplicate MoMo parking callback: {trans_id}")
            return True, 'Already processed'
        
        # ✅ BƯỚC 2: Lock vehicle row
        cursor.execute("""
            SELECT id, license_plate, status, payment_status
            FROM vehicles WITH (UPDLOCK, ROWLOCK)
            WHERE id = ?
        """, [vehicle_id])
        
        row = cursor.fetchone()
        
        if not row:
            logger.error(f"❌ Vehicle not found: {vehicle_id}")
            return False, 'Vehicle not found'
        
        vehicle_status = row[2]
        payment_status = row[3]
        
        # ✅ BƯỚC 3: Xử lý theo result_code
        if result_code == 0:
            # Thanh toán thành công
            
            cursor.execute("""
                UPDATE vehicles
                SET status = 'exited',
                    exit_time = GETDATE(),
                    actual_fee = ?,
                    payment_status = 'paid',
                    payment_method = 'momo',
                    momo_trans_id = ?
                WHERE id = ?
            """, [amount, trans_id, vehicle_id])
            
            conn.commit()
            
            logger.info(f"✅ Parking payment completed: vehicle_id={vehicle_id} | amount={amount:,} đ")
            
            return True, 'Parking payment completed'
        
        else:
            # Thanh toán thất bại
            cursor.execute("""
                UPDATE vehicles
                SET payment_status = 'failed',
                    momo_trans_id = ?
                WHERE id = ?
            """, [trans_id, vehicle_id])
            
            conn.commit()
            
            logger.warning(f"⚠️ Parking payment failed: vehicle_id={vehicle_id} | result_code={result_code}")
            
            return True, 'Parking payment failed'
    
    except Exception as e:
        conn.rollback()
        logger.error(f"❌ Error processing MoMo parking callback: {e}")
        return False, f'Processing error: {str(e)}'


def payment_result_route():
    """
    ✅ PRODUCTION-READY: Route xử lý callback từ MoMo
    
    Thay thế route /payment/result trong app.py
    """
    
    # ═══════════════════════════════════════════════════════════════
    # POST = IPN callback từ MoMo gửi về server
    # ═══════════════════════════════════════════════════════════════
    if request.method == 'POST':
        data = request.get_json() or {}
        
        logger.info(f"[MoMo Callback] Received: {data.get('orderId', 'N/A')}")
        
        # ✅ BƯỚC 1: Verify signature
        if not verify_momo_ipn(data):
            logger.error(f"❌ Invalid MoMo signature: {data.get('orderId', 'N/A')}")
            return jsonify({
                'status': -1,
                'message': 'Invalid signature'
            }), 400
        
        # ✅ BƯỚC 2: Xử lý theo loại giao dịch
        order_id = data.get('orderId', '')
        
        conn = get_db()
        
        try:
            if order_id.startswith('TOPUP-'):
                # Nạp tiền
                success, message = process_momo_topup_callback(data, conn)
            
            elif order_id.startswith('PARKING-'):
                # Thanh toán phí đỗ xe
                success, message = process_momo_parking_callback(data, conn)
            
            else:
                logger.error(f"❌ Unknown order_id format: {order_id}")
                return jsonify({
                    'status': -1,
                    'message': 'Unknown order_id format'
                }), 400
            
            if success:
                return jsonify({
                    'status': 0,
                    'message': message
                })
            else:
                return jsonify({
                    'status': -1,
                    'message': message
                }), 500
        
        finally:
            conn.close()
    
    # ═══════════════════════════════════════════════════════════════
    # GET = redirect sau khi khách thanh toán xong
    # ═══════════════════════════════════════════════════════════════
    pay_url = request.args.get('pay_url')
    message = request.args.get('message', 'Xử lý thanh toán thành công')
    
    return render_template('payment/result.html', pay_url=pay_url, message=message)


# ═══════════════════════════════════════════════════════════════════════════
# CÁCH SỬ DỤNG TRONG APP.PY
# ═══════════════════════════════════════════════════════════════════════════
"""
# Trong app.py, thay thế route cũ:

from fix_payment_webhook import payment_result_route

@app.route('/payment/result', methods=['GET', 'POST'])
def payment_result():
    return payment_result_route()
"""

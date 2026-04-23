"""
═══════════════════════════════════════════════════════════════════════════
FIX PAYMENT WEBHOOK - DUAL-MODE VERSION
═══════════════════════════════════════════════════════════════════════════
Production-ready webhook với hỗ trợ cả PostgreSQL và SQL Server
═══════════════════════════════════════════════════════════════════════════
"""

import logging
from datetime import datetime
from flask import request, jsonify, render_template
from momo import verify_momo_ipn
from db_utils import get_db, return_pg_connection, IS_POSTGRESQL, sql_now, sql_lock_row

logger = logging.getLogger(__name__)

def process_momo_topup_callback(data, conn):
    """
    ✅ Xử lý callback nạp tiền MoMo với idempotency (Dual-mode)
    
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
            WHERE momo_trans_id = %s
        """ if IS_POSTGRESQL else """
            SELECT id, status
            FROM topup_transactions
            WHERE momo_trans_id = ?
        """, [trans_id])
        
        existing = cursor.fetchone()
        
        if existing:
            logger.warning(f"⚠️ Duplicate MoMo callback: {trans_id} - Already processed")
            return True, 'Already processed'
        
        # ✅ BƯỚC 2: Lock row topup_transactions
        cursor.execute(f"""
            SELECT id, card_id, amount, status
            FROM topup_transactions {sql_lock_row()}
            WHERE transaction_id = {'%s' if IS_POSTGRESQL else '?'}
        """, [order_id])
        
        row = cursor.fetchone()
        
        if not row:
            logger.error(f"❌ Transaction not found: {order_id}")
            return False, 'Transaction not found'
        
        topup_id = row[0]
        card_id = row[1]
        topup_amount = row[2]
        status = row[3]
        
        # Kiểm tra đã completed chưa (double check)
        if status == 'completed':
            logger.warning(f"⚠️ Transaction already completed: {order_id}")
            return True, 'Already completed'
        
        # ✅ BƯỚC 3: Xử lý theo result_code
        if result_code == 0:
            # Thanh toán thành công
            
            # 3.1. Cập nhật topup_transactions
            cursor.execute(f"""
                UPDATE topup_transactions
                SET status = 'completed',
                    momo_trans_id = {'%s' if IS_POSTGRESQL else '?'},
                    completed_at = {sql_now()}
                WHERE id = {'%s' if IS_POSTGRESQL else '?'}
            """, [trans_id, topup_id])
            
            # 3.2. Lock card để tránh race condition
            cursor.execute(f"""
                SELECT id, balance
                FROM cards {sql_lock_row()}
                WHERE id = {'%s' if IS_POSTGRESQL else '?'}
            """, [card_id])
            
            card_row = cursor.fetchone()
            
            if not card_row:
                logger.error(f"❌ Card not found: {card_id}")
                conn.rollback()
                return False, 'Card not found'
            
            card_balance_before = card_row[1] or 0
            
            # 3.3. Cộng tiền vào thẻ
            cursor.execute(f"""
                UPDATE cards
                SET balance = balance + {'%s' if IS_POSTGRESQL else '?'}
                WHERE id = {'%s' if IS_POSTGRESQL else '?'}
            """, [topup_amount, card_id])
            
            # 3.4. Ghi log vào balance_history
            cursor.execute(f"""
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
                VALUES ({'%s, %s, %s, %s, %s, %s, %s, ' + sql_now() + ', %s, %s' if IS_POSTGRESQL else '?, ?, ?, ?, ?, ?, ?, ' + sql_now() + ', ?, ?'})
            """, [
                card_id, 
                topup_amount, 
                card_balance_before,
                card_balance_before + topup_amount,
                'topup',
                f'Nạp tiền MoMo - {order_id}',
                order_id,
                'MOMO_CALLBACK',
                request.remote_addr
            ])
            
            # 3.5. Commit transaction
            conn.commit()
            
            logger.info(f"✅ Topup completed: {order_id} | card_id={card_id} | amount={topup_amount:,} đ")
            
            return True, 'Topup completed successfully'
        
        else:
            # Thanh toán thất bại
            cursor.execute(f"""
                UPDATE topup_transactions
                SET status = 'failed',
                    momo_trans_id = {'%s' if IS_POSTGRESQL else '?'},
                    completed_at = {sql_now()}
                WHERE id = {'%s' if IS_POSTGRESQL else '?'}
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
    ✅ Xử lý callback thanh toán phí đỗ xe MoMo (Dual-mode)
    
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
        cursor.execute(f"""
            SELECT id, payment_status
            FROM vehicles
            WHERE id = {'%s' if IS_POSTGRESQL else '?'} AND momo_trans_id = {'%s' if IS_POSTGRESQL else '?'}
        """, [vehicle_id, trans_id])
        
        existing = cursor.fetchone()
        
        if existing:
            logger.warning(f"⚠️ Duplicate MoMo parking callback: {trans_id}")
            return True, 'Already processed'
        
        # ✅ BƯỚC 2: Lock vehicle row
        cursor.execute(f"""
            SELECT id, license_plate, status, payment_status
            FROM vehicles {sql_lock_row()}
            WHERE id = {'%s' if IS_POSTGRESQL else '?'}
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
            
            cursor.execute(f"""
                UPDATE vehicles
                SET status = 'exited',
                    exit_time = {sql_now()},
                    actual_fee = {'%s' if IS_POSTGRESQL else '?'},
                    payment_status = 'paid',
                    payment_method = 'momo',
                    momo_trans_id = {'%s' if IS_POSTGRESQL else '?'}
                WHERE id = {'%s' if IS_POSTGRESQL else '?'}
            """, [amount, trans_id, vehicle_id])
            
            conn.commit()
            
            logger.info(f"✅ Parking payment completed: vehicle_id={vehicle_id} | amount={amount:,} đ")
            
            return True, 'Parking payment completed'
        
        else:
            # Thanh toán thất bại
            cursor.execute(f"""
                UPDATE vehicles
                SET payment_status = 'failed',
                    momo_trans_id = {'%s' if IS_POSTGRESQL else '?'}
                WHERE id = {'%s' if IS_POSTGRESQL else '?'}
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
    ✅ PRODUCTION-READY: Route xử lý callback từ MoMo (Dual-mode)
    
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
            if IS_POSTGRESQL:
                return_pg_connection(conn)
            else:
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
# Trong app.py, thay thế import:

from fix_payment_webhook_dual import payment_result_route

@app.route('/payment/result', methods=['GET', 'POST'])
def payment_result():
    return payment_result_route()
"""

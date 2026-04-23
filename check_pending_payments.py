"""
═══════════════════════════════════════════════════════════════════════════
CRONJOB: CHECK PENDING PAYMENTS
═══════════════════════════════════════════════════════════════════════════
Script này chạy định kỳ (mỗi 5 phút) để kiểm tra các giao dịch pending
và query lại trạng thái từ MoMo nếu webhook bị miss
═══════════════════════════════════════════════════════════════════════════
"""

import os
import pyodbc
import requests
import hmac
import hashlib
import json
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# ═══════════════════════════════════════════════════════════════════════════
# LOGGING
# ═══════════════════════════════════════════════════════════════════════════

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('check_pending_payments.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════════════════

DB_SERVER = os.getenv('DB_SERVER', r'LAPTOP-3J6T1I18\SQLEXPRESS01')
DB_DATABASE = os.getenv('DB_DATABASE', 'ParkingManagement')
DB_DRIVER = 'ODBC Driver 17 for SQL Server'

MOMO_QUERY_ENDPOINT = os.getenv('MOMO_QUERY_ENDPOINT', 'https://test-payment.momo.vn/v2/gateway/api/query')
MOMO_PARTNER_CODE = os.getenv('MOMO_PARTNER_CODE', '')
MOMO_ACCESS_KEY = os.getenv('MOMO_ACCESS_KEY', '')
MOMO_SECRET_KEY = os.getenv('MOMO_SECRET_KEY', '')

# ═══════════════════════════════════════════════════════════════════════════
# DATABASE
# ═══════════════════════════════════════════════════════════════════════════

def get_db():
    """Tạo kết nối database"""
    conn = pyodbc.connect(
        f'DRIVER={{{DB_DRIVER}}};'
        f'SERVER={DB_SERVER};'
        f'DATABASE={DB_DATABASE};'
        f'Trusted_Connection=yes;'
    )
    conn.setdecoding(pyodbc.SQL_WCHAR, encoding='utf-16-le')
    conn.setencoding(encoding='utf-16-le')
    return conn

# ═══════════════════════════════════════════════════════════════════════════
# MOMO API
# ═══════════════════════════════════════════════════════════════════════════

def _build_signature(raw: str) -> str:
    """Tạo HMAC SHA256 signature"""
    return hmac.new(
        bytes(MOMO_SECRET_KEY, 'ascii'),
        bytes(raw, 'ascii'),
        hashlib.sha256
    ).hexdigest()


def query_momo_transaction_status(order_id: str, request_id: str) -> dict:
    """
    Query trạng thái giao dịch từ MoMo API
    
    Args:
        order_id: Mã đơn hàng (TOPUP-xxx hoặc PARKING-xxx)
        request_id: Request ID khi tạo payment
    
    Returns:
        {
            'success': True/False,
            'result_code': 0/other,
            'trans_id': 'xxx',
            'message': 'xxx'
        }
    """
    
    # Tạo signature
    raw_signature = (
        f"accessKey={MOMO_ACCESS_KEY}"
        f"&orderId={order_id}"
        f"&partnerCode={MOMO_PARTNER_CODE}"
        f"&requestId={request_id}"
    )
    
    signature = _build_signature(raw_signature)
    
    payload = {
        'partnerCode': MOMO_PARTNER_CODE,
        'requestId': request_id,
        'orderId': order_id,
        'lang': 'vi',
        'signature': signature
    }
    
    try:
        response = requests.post(
            MOMO_QUERY_ENDPOINT,
            data=json.dumps(payload),
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        response.raise_for_status()
        result = response.json()
        
        return {
            'success': True,
            'result_code': result.get('resultCode', -1),
            'trans_id': result.get('transId', ''),
            'message': result.get('message', ''),
            'amount': result.get('amount', 0)
        }
    
    except Exception as e:
        logger.error(f"❌ Error querying MoMo: {e}")
        return {
            'success': False,
            'result_code': -1,
            'trans_id': '',
            'message': str(e)
        }

# ═══════════════════════════════════════════════════════════════════════════
# MAIN LOGIC
# ═══════════════════════════════════════════════════════════════════════════

def check_pending_topup_transactions():
    """
    Kiểm tra các giao dịch nạp tiền pending > 10 phút
    """
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Lấy các giao dịch pending quá 10 phút, trong vòng 24h
        cursor.execute("""
            SELECT 
                id, 
                transaction_id, 
                card_id,
                amount, 
                payment_method,
                created_at,
                DATEDIFF(MINUTE, created_at, GETDATE()) AS minutes_pending
            FROM topup_transactions
            WHERE status = 'pending'
              AND payment_method = 'momo'
              AND created_at < DATEADD(MINUTE, -10, GETDATE())
              AND created_at > DATEADD(HOUR, -24, GETDATE())
            ORDER BY created_at ASC
        """)
        
        pending_txns = cursor.fetchall()
        
        logger.info(f"📊 Found {len(pending_txns)} pending topup transactions")
        
        for txn in pending_txns:
            txn_id, order_id, card_id, amount, payment_method, created_at, minutes_pending = txn
            
            logger.info(f"🔍 Checking: {order_id} | {minutes_pending} minutes pending")
            
            # Query trạng thái từ MoMo
            # TODO: Cần lưu request_id khi tạo payment để query
            # Hiện tại tạm thời skip vì không có request_id
            
            # result = query_momo_transaction_status(order_id, request_id)
            
            # if result['success'] and result['result_code'] == 0:
            #     # Thanh toán thành công, cập nhật database
            #     trans_id = result['trans_id']
            #     
            #     # Lock và cập nhật
            #     cursor.execute("""
            #         UPDATE topup_transactions
            #         SET status = 'completed',
            #             momo_trans_id = ?,
            #             completed_at = GETDATE()
            #         WHERE id = ?
            #     """, [trans_id, txn_id])
            #     
            #     # Cộng tiền vào thẻ
            #     cursor.execute("""
            #         UPDATE cards
            #         SET balance = balance + ?
            #         WHERE id = ?
            #     """, [amount, card_id])
            #     
            #     # Ghi log
            #     cursor.execute("""
            #         INSERT INTO balance_history (
            #             card_id, amount, type, description, transaction_id, created_at, created_by
            #         )
            #         VALUES (?, ?, 'topup', ?, ?, GETDATE(), 'CRONJOB')
            #     """, [card_id, amount, f'Nạp tiền MoMo (recovered) - {order_id}', order_id])
            #     
            #     conn.commit()
            #     
            #     logger.info(f"✅ Recovered: {order_id} | {amount:,} đ")
            
            # elif result['success'] and result['result_code'] != 0:
            #     # Thanh toán thất bại
            #     cursor.execute("""
            #         UPDATE topup_transactions
            #         SET status = 'failed',
            #             completed_at = GETDATE()
            #         WHERE id = ?
            #     """, [txn_id])
            #     
            #     conn.commit()
            #     
            #     logger.warning(f"⚠️ Failed: {order_id} | result_code={result['result_code']}")
            
            # Nếu pending quá 30 phút, gửi alert
            if minutes_pending > 30:
                logger.error(f"🚨 ALERT: Transaction pending > 30 minutes: {order_id}")
                # TODO: Gửi email/SMS alert cho admin
    
    except Exception as e:
        logger.error(f"❌ Error checking pending topup: {e}")
        conn.rollback()
    
    finally:
        conn.close()


def check_pending_parking_payments():
    """
    Kiểm tra các xe đang chờ thanh toán MoMo
    """
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Lấy các xe đang chờ thanh toán MoMo
        cursor.execute("""
            SELECT 
                id,
                license_plate,
                actual_fee,
                entry_time,
                DATEDIFF(MINUTE, entry_time, GETDATE()) AS minutes_parked
            FROM vehicles
            WHERE status = 'parked'
              AND payment_status = 'pending'
              AND payment_method = 'momo'
              AND entry_time > DATEADD(HOUR, -24, GETDATE())
            ORDER BY entry_time ASC
        """)
        
        pending_vehicles = cursor.fetchall()
        
        logger.info(f"📊 Found {len(pending_vehicles)} pending parking payments")
        
        for vehicle in pending_vehicles:
            vehicle_id, license_plate, actual_fee, entry_time, minutes_parked = vehicle
            
            logger.info(f"🔍 Checking vehicle: {license_plate} | {minutes_parked} minutes parked")
            
            # TODO: Query MoMo API để kiểm tra trạng thái
            # Tương tự như topup
    
    except Exception as e:
        logger.error(f"❌ Error checking pending parking: {e}")
        conn.rollback()
    
    finally:
        conn.close()


def send_alert_email(subject: str, message: str):
    """
    Gửi email alert cho admin
    
    TODO: Implement email sending
    """
    logger.info(f"📧 Alert: {subject} | {message}")
    # TODO: Dùng Flask-Mail hoặc SendGrid


def generate_report():
    """
    Tạo báo cáo tổng hợp
    """
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Thống kê pending transactions
        cursor.execute("""
            SELECT 
                COUNT(*) AS total,
                SUM(amount) AS total_amount,
                MIN(DATEDIFF(MINUTE, created_at, GETDATE())) AS min_minutes,
                MAX(DATEDIFF(MINUTE, created_at, GETDATE())) AS max_minutes,
                AVG(DATEDIFF(MINUTE, created_at, GETDATE())) AS avg_minutes
            FROM topup_transactions
            WHERE status = 'pending'
              AND payment_method = 'momo'
              AND created_at > DATEADD(HOUR, -24, GETDATE())
        """)
        
        row = cursor.fetchone()
        
        if row and row[0] > 0:
            total, total_amount, min_minutes, max_minutes, avg_minutes = row
            
            logger.info("═" * 80)
            logger.info("📊 PENDING TRANSACTIONS REPORT")
            logger.info("═" * 80)
            logger.info(f"Total pending: {total}")
            logger.info(f"Total amount: {total_amount:,} đ")
            logger.info(f"Min pending time: {min_minutes} minutes")
            logger.info(f"Max pending time: {max_minutes} minutes")
            logger.info(f"Avg pending time: {avg_minutes} minutes")
            logger.info("═" * 80)
            
            # Gửi alert nếu có transaction pending quá 30 phút
            if max_minutes > 30:
                send_alert_email(
                    subject="🚨 ALERT: Pending transactions > 30 minutes",
                    message=f"Có {total} giao dịch pending, lâu nhất {max_minutes} phút"
                )
        else:
            logger.info("✅ No pending transactions")
    
    except Exception as e:
        logger.error(f"❌ Error generating report: {e}")
    
    finally:
        conn.close()


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

def main():
    """
    Main function - chạy tất cả checks
    """
    logger.info("═" * 80)
    logger.info("🚀 STARTING PENDING PAYMENTS CHECK")
    logger.info(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("═" * 80)
    
    try:
        # 1. Check pending topup transactions
        check_pending_topup_transactions()
        
        # 2. Check pending parking payments
        check_pending_parking_payments()
        
        # 3. Generate report
        generate_report()
        
        logger.info("✅ CHECK COMPLETED")
    
    except Exception as e:
        logger.error(f"❌ CRITICAL ERROR: {e}")
        send_alert_email(
            subject="🚨 CRITICAL: Cronjob failed",
            message=f"Error: {str(e)}"
        )
    
    logger.info("═" * 80)


if __name__ == '__main__':
    main()

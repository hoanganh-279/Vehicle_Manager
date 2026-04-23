"""
═══════════════════════════════════════════════════════════════════════════
SCRIPT ĐỐI SOÁT GIAO DỊCH "LỠ"
═══════════════════════════════════════════════════════════════════════════
Chạy sau khi rollback để xử lý các giao dịch bị lỡ trong thời gian lỗi
═══════════════════════════════════════════════════════════════════════════
"""

import os
import pyodbc
import logging
from datetime import datetime

# ═══════════════════════════════════════════════════════════════════════════
# LOGGING
# ═══════════════════════════════════════════════════════════════════════════

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('reconcile_transactions.log'),
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
# MAIN LOGIC
# ═══════════════════════════════════════════════════════════════════════════

def reconcile_pending_transactions(start_time, end_time):
    """
    Đối soát các giao dịch pending trong khoảng thời gian lỗi
    
    Args:
        start_time: Thời gian bắt đầu lỗi (format: 'YYYY-MM-DD HH:MM:SS')
        end_time: Thời gian kết thúc lỗi (format: 'YYYY-MM-DD HH:MM:SS')
    """
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        logger.info("═" * 80)
        logger.info("ĐỐI SOÁT GIAO DỊCH 'LỠ'")
        logger.info(f"Thời gian lỗi: {start_time} → {end_time}")
        logger.info("═" * 80)
        
        # Lấy các giao dịch pending trong khoảng thời gian lỗi
        cursor.execute("""
            SELECT 
                id,
                transaction_id,
                card_id,
                amount,
                payment_method,
                created_at
            FROM topup_transactions
            WHERE status = 'pending'
              AND payment_method = 'momo'
              AND created_at BETWEEN ? AND ?
            ORDER BY created_at ASC
        """, [start_time, end_time])
        
        pending_txns = cursor.fetchall()
        
        logger.info(f"Số giao dịch pending: {len(pending_txns)}")
        logger.info("═" * 80)
        
        if len(pending_txns) == 0:
            logger.info("✅ Không có giao dịch nào bị lỡ")
            return
        
        # Thống kê
        total_amount = sum(txn[3] for txn in pending_txns)
        logger.info(f"Tổng số tiền: {total_amount:,} đ")
        logger.info("")
        
        # Xử lý từng giao dịch
        processed = 0
        completed = 0
        failed = 0
        skipped = 0
        
        for txn in pending_txns:
            txn_id, order_id, card_id, amount, payment_method, created_at = txn
            
            logger.info(f"{'─' * 80}")
            logger.info(f"📋 Giao dịch #{processed + 1}/{len(pending_txns)}")
            logger.info(f"   Order ID: {order_id}")
            logger.info(f"   Card ID: {card_id}")
            logger.info(f"   Amount: {amount:,} đ")
            logger.info(f"   Created: {created_at}")
            logger.info("")
            
            # Lấy thông tin card
            cursor.execute("""
                SELECT name, phone, balance
                FROM cards
                WHERE id = ?
            """, [card_id])
            
            card_row = cursor.fetchone()
            
            if card_row:
                card_name, card_phone, card_balance = card_row
                logger.info(f"   Card: {card_name} ({card_phone})")
                logger.info(f"   Số dư hiện tại: {card_balance:,} đ")
                logger.info("")
            
            # Yêu cầu admin xác nhận
            print(f"❓ Giao dịch {order_id} đã thanh toán thành công chưa?")
            print(f"   (Kiểm tra trên MoMo dashboard)")
            print(f"   1. Có - Cộng tiền vào ví")
            print(f"   2. Không - Đánh dấu failed")
            print(f"   3. Skip - Xử lý sau")
            print("")
            
            choice = input("   Chọn (1/2/3): ").strip()
            
            if choice == '1':
                # Cộng tiền
                try:
                    cursor.execute("""
                        UPDATE topup_transactions
                        SET status = 'completed',
                            completed_at = GETDATE()
                        WHERE id = ?
                    """, [txn_id])
                    
                    cursor.execute("""
                        UPDATE cards
                        SET balance = balance + ?
                        WHERE id = ?
                    """, [amount, card_id])
                    
                    conn.commit()
                    
                    new_balance = card_balance + amount
                    
                    logger.info(f"   ✅ Đã cộng {amount:,} đ vào card {card_id}")
                    logger.info(f"   Số dư mới: {new_balance:,} đ")
                    
                    completed += 1
                
                except Exception as e:
                    logger.error(f"   ❌ Lỗi: {e}")
                    conn.rollback()
            
            elif choice == '2':
                # Đánh dấu failed
                try:
                    cursor.execute("""
                        UPDATE topup_transactions
                        SET status = 'failed',
                            completed_at = GETDATE()
                        WHERE id = ?
                    """, [txn_id])
                    
                    conn.commit()
                    
                    logger.info(f"   ❌ Đã đánh dấu failed")
                    
                    failed += 1
                
                except Exception as e:
                    logger.error(f"   ❌ Lỗi: {e}")
                    conn.rollback()
            
            else:
                logger.info(f"   ⏭️  Skip - Sẽ xử lý sau")
                skipped += 1
            
            processed += 1
            print("")
        
        # Tổng kết
        logger.info("═" * 80)
        logger.info("ĐỐI SOÁT HOÀN TẤT")
        logger.info("═" * 80)
        logger.info(f"Tổng số giao dịch: {len(pending_txns)}")
        logger.info(f"  ✅ Completed: {completed}")
        logger.info(f"  ❌ Failed: {failed}")
        logger.info(f"  ⏭️  Skipped: {skipped}")
        logger.info(f"Tổng số tiền đã cộng: {sum(txn[3] for txn in pending_txns[:completed]):,} đ")
        logger.info("═" * 80)
        
        # Verify balance integrity
        logger.info("")
        logger.info("Đang verify balance integrity...")
        
        cursor.execute("""
            SELECT 
                c.id,
                c.name,
                c.balance,
                ISNULL(SUM(
                    CASE 
                        WHEN t.status = 'completed' THEN t.amount
                        ELSE 0
                    END
                ), 0) AS total_topup
            FROM cards c
            LEFT JOIN topup_transactions t ON c.id = t.card_id
            WHERE c.id IN (
                SELECT DISTINCT card_id
                FROM topup_transactions
                WHERE created_at BETWEEN ? AND ?
            )
            GROUP BY c.id, c.name, c.balance
        """, [start_time, end_time])
        
        cards = cursor.fetchall()
        
        for card in cards:
            card_id, card_name, balance, total_topup = card
            logger.info(f"Card {card_id} ({card_name}): Balance={balance:,} | Total Topup={total_topup:,}")
        
        logger.info("")
        logger.info("✅ Đối soát hoàn tất!")
    
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        conn.rollback()
    
    finally:
        conn.close()


def main():
    """
    Main function
    """
    print("═" * 80)
    print("SCRIPT ĐỐI SOÁT GIAO DỊCH 'LỠ'")
    print("═" * 80)
    print("")
    print("Script này sẽ giúp bạn đối soát các giao dịch bị lỡ")
    print("trong khoảng thời gian hệ thống bị lỗi.")
    print("")
    print("Bạn cần nhập:")
    print("  1. Thời gian bắt đầu lỗi (khi deploy)")
    print("  2. Thời gian kết thúc lỗi (khi rollback xong)")
    print("")
    print("Format: YYYY-MM-DD HH:MM:SS")
    print("Ví dụ: 2026-04-16 10:00:00")
    print("")
    
    # Nhập thời gian
    start_time = input("Thời gian bắt đầu lỗi: ").strip()
    end_time = input("Thời gian kết thúc lỗi: ").strip()
    
    # Validate format
    try:
        datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
        datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        print("")
        print("❌ Format thời gian không đúng!")
        print("Vui lòng dùng format: YYYY-MM-DD HH:MM:SS")
        return
    
    print("")
    print(f"Sẽ đối soát giao dịch từ {start_time} đến {end_time}")
    print("")
    
    confirm = input("Tiếp tục? (y/n): ").strip().lower()
    
    if confirm != 'y':
        print("Đã hủy.")
        return
    
    print("")
    
    # Chạy đối soát
    reconcile_pending_transactions(start_time, end_time)


if __name__ == '__main__':
    main()

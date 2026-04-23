"""
═══════════════════════════════════════════════════════════════════════════
TEST RACE CONDITION - CONCURRENT REQUESTS
═══════════════════════════════════════════════════════════════════════════
Script này test xem hệ thống có bị race condition không
Gửi nhiều request đồng thời để thanh toán cùng 1 xe
═══════════════════════════════════════════════════════════════════════════
"""

import requests
import threading
import time
import uuid
from datetime import datetime

# ═══════════════════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════════════════

BASE_URL = 'http://localhost:5000'
VEHICLE_ID = 1  # ← Thay bằng ID xe thực tế trong database
CARD_ID = 1     # ← Thay bằng ID thẻ thực tế

# ═══════════════════════════════════════════════════════════════════════════
# TEST FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def test_concurrent_parking_exit(thread_id, results):
    """
    Test thanh toán xe ra bãi đồng thời
    
    Args:
        thread_id: ID của thread
        results: list để lưu kết quả
    """
    # Tạo idempotency key unique cho mỗi thread
    idempotency_key = str(uuid.uuid4())
    
    headers = {
        'Content-Type': 'application/json',
        'X-Idempotency-Key': idempotency_key
    }
    
    payload = {
        'action': 'exit',
        'vehicle_id': VEHICLE_ID,
        'payment_method': 'card',
        'card_id': CARD_ID
    }
    
    try:
        start_time = time.time()
        
        response = requests.post(
            f'{BASE_URL}/parking/exit',
            json=payload,
            headers=headers,
            timeout=10
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        result = {
            'thread_id': thread_id,
            'status_code': response.status_code,
            'response': response.json(),
            'duration': duration,
            'timestamp': datetime.now().isoformat()
        }
        
        results.append(result)
        
        print(f"Thread {thread_id}: {response.status_code} | {duration:.2f}s | {response.json().get('message', 'N/A')}")
    
    except Exception as e:
        result = {
            'thread_id': thread_id,
            'status_code': 'ERROR',
            'response': {'error': str(e)},
            'duration': 0,
            'timestamp': datetime.now().isoformat()
        }
        
        results.append(result)
        
        print(f"Thread {thread_id}: ERROR | {str(e)}")


def test_concurrent_topup(thread_id, results):
    """
    Test nạp tiền đồng thời
    
    Args:
        thread_id: ID của thread
        results: list để lưu kết quả
    """
    payload = {
        'card_id': CARD_ID,
        'amount': 100000,
        'payment_method': 'momo'
    }
    
    try:
        start_time = time.time()
        
        response = requests.post(
            f'{BASE_URL}/card/topup',
            json=payload,
            timeout=10
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        result = {
            'thread_id': thread_id,
            'status_code': response.status_code,
            'response': response.json(),
            'duration': duration,
            'timestamp': datetime.now().isoformat()
        }
        
        results.append(result)
        
        print(f"Thread {thread_id}: {response.status_code} | {duration:.2f}s")
    
    except Exception as e:
        result = {
            'thread_id': thread_id,
            'status_code': 'ERROR',
            'response': {'error': str(e)},
            'duration': 0,
            'timestamp': datetime.now().isoformat()
        }
        
        results.append(result)
        
        print(f"Thread {thread_id}: ERROR | {str(e)}")


def test_duplicate_idempotency_key():
    """
    Test xem idempotency key có hoạt động không
    Gửi 2 request với cùng idempotency key
    """
    print("\n" + "═" * 80)
    print("TEST: DUPLICATE IDEMPOTENCY KEY")
    print("═" * 80)
    
    idempotency_key = str(uuid.uuid4())
    
    headers = {
        'Content-Type': 'application/json',
        'X-Idempotency-Key': idempotency_key
    }
    
    payload = {
        'action': 'exit',
        'vehicle_id': VEHICLE_ID,
        'payment_method': 'cash'
    }
    
    # Request 1
    print("\n📤 Sending request 1...")
    response1 = requests.post(
        f'{BASE_URL}/parking/exit',
        json=payload,
        headers=headers
    )
    
    print(f"✅ Response 1: {response1.status_code} | {response1.json()}")
    
    # Request 2 (cùng idempotency key)
    print("\n📤 Sending request 2 (same idempotency key)...")
    response2 = requests.post(
        f'{BASE_URL}/parking/exit',
        json=payload,
        headers=headers
    )
    
    print(f"✅ Response 2: {response2.status_code} | {response2.json()}")
    
    # Kiểm tra
    if response1.json() == response2.json():
        print("\n✅ PASS: Idempotency key hoạt động đúng!")
    else:
        print("\n❌ FAIL: Idempotency key KHÔNG hoạt động!")
    
    print("═" * 80)


# ═══════════════════════════════════════════════════════════════════════════
# MAIN TEST SUITE
# ═══════════════════════════════════════════════════════════════════════════

def run_concurrent_test(test_func, num_threads=10, test_name=""):
    """
    Chạy test với nhiều threads đồng thời
    
    Args:
        test_func: Hàm test
        num_threads: Số lượng threads
        test_name: Tên test
    """
    print("\n" + "═" * 80)
    print(f"TEST: {test_name}")
    print(f"Threads: {num_threads}")
    print("═" * 80)
    
    results = []
    threads = []
    
    # Tạo và start threads
    print(f"\n🚀 Starting {num_threads} concurrent requests...")
    start_time = time.time()
    
    for i in range(num_threads):
        thread = threading.Thread(target=test_func, args=(i+1, results))
        threads.append(thread)
        thread.start()
    
    # Đợi tất cả threads hoàn thành
    for thread in threads:
        thread.join()
    
    end_time = time.time()
    total_duration = end_time - start_time
    
    # Phân tích kết quả
    print("\n" + "─" * 80)
    print("📊 RESULTS")
    print("─" * 80)
    
    success_count = sum(1 for r in results if r['status_code'] == 200 and r['response'].get('success'))
    fail_count = len(results) - success_count
    
    print(f"Total requests: {len(results)}")
    print(f"Success: {success_count}")
    print(f"Failed: {fail_count}")
    print(f"Total duration: {total_duration:.2f}s")
    print(f"Avg duration: {sum(r['duration'] for r in results) / len(results):.2f}s")
    
    # Kiểm tra race condition
    if success_count > 1:
        print("\n❌ FAIL: Race condition detected!")
        print(f"   → {success_count} requests succeeded (should be only 1)")
    elif success_count == 1:
        print("\n✅ PASS: No race condition!")
    else:
        print("\n⚠️  WARNING: All requests failed")
    
    print("═" * 80)
    
    return results


def main():
    """
    Main test suite
    """
    print("\n" + "═" * 80)
    print("🧪 RACE CONDITION TEST SUITE")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("═" * 80)
    
    # Test 1: Concurrent parking exit
    print("\n\n")
    run_concurrent_test(
        test_func=test_concurrent_parking_exit,
        num_threads=10,
        test_name="CONCURRENT PARKING EXIT (10 threads)"
    )
    
    # Test 2: Concurrent topup
    # print("\n\n")
    # run_concurrent_test(
    #     test_func=test_concurrent_topup,
    #     num_threads=5,
    #     test_name="CONCURRENT TOPUP (5 threads)"
    # )
    
    # Test 3: Duplicate idempotency key
    print("\n\n")
    test_duplicate_idempotency_key()
    
    print("\n\n" + "═" * 80)
    print("✅ TEST SUITE COMPLETED")
    print("═" * 80)


if __name__ == '__main__':
    main()

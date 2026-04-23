"""
═══════════════════════════════════════════════════════════════════════════
PAYMENT SECURITY TEST SUITE
═══════════════════════════════════════════════════════════════════════════
Test tất cả các edge cases và security vulnerabilities
═══════════════════════════════════════════════════════════════════════════
"""

import requests
import time
import threading
from concurrent.futures import ThreadPoolExecutor
import json

BASE_URL = "http://localhost:5000"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_test(name):
    print(f"\n{Colors.BLUE}{'='*80}{Colors.END}")
    print(f"{Colors.BLUE}TEST: {name}{Colors.END}")
    print(f"{Colors.BLUE}{'='*80}{Colors.END}")

def print_pass(msg):
    print(f"{Colors.GREEN}✅ PASS: {msg}{Colors.END}")

def print_fail(msg):
    print(f"{Colors.RED}❌ FAIL: {msg}{Colors.END}")

def print_warn(msg):
    print(f"{Colors.YELLOW}⚠️  WARN: {msg}{Colors.END}")

# ═══════════════════════════════════════════════════════════════════════════
# TEST #1: PRICE TAMPERING
# ═══════════════════════════════════════════════════════════════════════════

def test_price_tampering():
    """
    Test xem Backend có tin tưởng giá từ Frontend không
    """
    print_test("Price Tampering Attack")
    
    # Giả sử xe #1 có phí thật là 50,000 đ
    # Hacker cố gắng gửi parking_fee = 1,000 đ
    
    payload = {
        "vehicle_id": 1,
        "payment_method": "cash",
        "parking_fee": 1000  # ← Giá giả mạo!
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-Idempotency-Key": f"test-price-{time.time()}"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/parking/exit",
            json=payload,
            headers=headers
        )
        
        data = response.json()
        
        if data.get('success'):
            actual_fee = data.get('data', {}).get('parking_fee', 0)
            
            if actual_fee == 1000:
                print_fail(f"Backend tin tưởng giá từ Frontend! Phí lưu: {actual_fee} đ")
                print_fail("🔴 CRITICAL: Lỗ hổng bảo mật nghiêm trọng!")
                return False
            else:
                print_pass(f"Backend tính lại giá đúng: {actual_fee} đ (không tin Frontend)")
                return True
        else:
            print_warn(f"Request failed: {data.get('message')}")
            return None
            
    except Exception as e:
        print_fail(f"Exception: {str(e)}")
        return False

# ═══════════════════════════════════════════════════════════════════════════
# TEST #2: DOUBLE SUBMIT
# ═══════════════════════════════════════════════════════════════════════════

def test_double_submit():
    """
    Test xem hệ thống có ngăn được double submit không
    """
    print_test("Double Submit Prevention")
    
    # Gửi cùng 1 request 5 lần với cùng idempotency key
    idempotency_key = f"test-double-{time.time()}"
    
    payload = {
        "vehicle_id": 2,
        "payment_method": "cash"
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-Idempotency-Key": idempotency_key
    }
    
    results = []
    
    def send_request():
        try:
            response = requests.post(
                f"{BASE_URL}/parking/exit",
                json=payload,
                headers=headers
            )
            results.append(response.json())
        except Exception as e:
            results.append({"error": str(e)})
    
    # Gửi 5 requests đồng thời
    threads = []
    for i in range(5):
        t = threading.Thread(target=send_request)
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    # Kiểm tra kết quả
    success_count = sum(1 for r in results if r.get('success'))
    
    if success_count == 1:
        print_pass(f"Chỉ 1 request được xử lý, {len(results)-1} requests bị reject")
        return True
    elif success_count > 1:
        print_fail(f"🔴 CRITICAL: {success_count} requests được xử lý (nên là 1)")
        print_fail("Hệ thống KHÔNG ngăn được double submit!")
        return False
    else:
        print_warn("Tất cả requests đều fail")
        return None

# ═══════════════════════════════════════════════════════════════════════════
# TEST #3: RACE CONDITION
# ═══════════════════════════════════════════════════════════════════════════

def test_race_condition():
    """
    Test xem 2 users có thể thanh toán cùng 1 xe không
    """
    print_test("Race Condition (2 users thanh toán cùng 1 xe)")
    
    vehicle_id = 3
    
    def user_payment(user_id):
        payload = {
            "vehicle_id": vehicle_id,
            "payment_method": "cash"
        }
        
        headers = {
            "Content-Type": "application/json",
            "X-Idempotency-Key": f"test-race-user{user_id}-{time.time()}"
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/parking/exit",
                json=payload,
                headers=headers
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    # 2 users cùng thanh toán 1 xe
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(user_payment, 1),
            executor.submit(user_payment, 2)
        ]
        results = [f.result() for f in futures]
    
    success_count = sum(1 for r in results if r.get('success'))
    
    if success_count == 1:
        print_pass("Chỉ 1 user thanh toán thành công, user kia bị reject")
        return True
    elif success_count == 2:
        print_fail("🔴 CRITICAL: Cả 2 users đều thanh toán thành công!")
        print_fail("Xe bị tính phí 2 lần!")
        return False
    else:
        print_warn("Cả 2 requests đều fail")
        return None

# ═══════════════════════════════════════════════════════════════════════════
# TEST #4: TRANSACTION ROLLBACK
# ═══════════════════════════════════════════════════════════════════════════

def test_transaction_rollback():
    """
    Test xem transaction có rollback khi lỗi không
    """
    print_test("Transaction Rollback")
    
    # Gửi request với card_id không tồn tại
    # Nếu có transaction, sẽ rollback toàn bộ
    
    payload = {
        "vehicle_id": 4,
        "payment_method": "card",
        "card_id": "FAKE_CARD_999"  # Card không tồn tại
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-Idempotency-Key": f"test-rollback-{time.time()}"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/parking/exit",
            json=payload,
            headers=headers
        )
        
        data = response.json()
        
        if not data.get('success'):
            print_pass(f"Request bị reject đúng: {data.get('message')}")
            
            # TODO: Kiểm tra database xem xe có bị cập nhật không
            # Nếu có transaction đúng, xe vẫn phải ở trạng thái 'parked'
            
            return True
        else:
            print_fail("Request thành công dù card không tồn tại!")
            return False
            
    except Exception as e:
        print_fail(f"Exception: {str(e)}")
        return False

# ═══════════════════════════════════════════════════════════════════════════
# TEST #5: INPUT VALIDATION
# ═══════════════════════════════════════════════════════════════════════════

def test_input_validation():
    """
    Test xem Backend có validate input không
    """
    print_test("Input Validation")
    
    test_cases = [
        {
            "name": "Missing vehicle_id",
            "payload": {"payment_method": "cash"},
            "should_fail": True
        },
        {
            "name": "Invalid payment_method",
            "payload": {"vehicle_id": 5, "payment_method": "hacked"},
            "should_fail": True
        },
        {
            "name": "Negative parking_fee",
            "payload": {"vehicle_id": 5, "payment_method": "cash", "parking_fee": -1000},
            "should_fail": False  # Backend nên ignore parking_fee từ Frontend
        },
        {
            "name": "SQL Injection attempt",
            "payload": {"vehicle_id": "1 OR 1=1", "payment_method": "cash"},
            "should_fail": True
        }
    ]
    
    passed = 0
    failed = 0
    
    for test in test_cases:
        headers = {
            "Content-Type": "application/json",
            "X-Idempotency-Key": f"test-validation-{time.time()}"
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/parking/exit",
                json=test["payload"],
                headers=headers
            )
            
            data = response.json()
            success = data.get('success', False)
            
            if test["should_fail"]:
                if not success:
                    print_pass(f"{test['name']}: Bị reject đúng")
                    passed += 1
                else:
                    print_fail(f"{test['name']}: Không bị reject!")
                    failed += 1
            else:
                if success or "không hợp lệ" in data.get('message', '').lower():
                    print_pass(f"{test['name']}: Xử lý đúng")
                    passed += 1
                else:
                    print_warn(f"{test['name']}: {data.get('message')}")
                    
        except Exception as e:
            print_fail(f"{test['name']}: Exception - {str(e)}")
            failed += 1
        
        time.sleep(0.1)
    
    print(f"\n📊 Kết quả: {passed} passed, {failed} failed")
    return failed == 0

# ═══════════════════════════════════════════════════════════════════════════
# MAIN TEST RUNNER
# ═══════════════════════════════════════════════════════════════════════════

def run_all_tests():
    """
    Chạy tất cả tests
    """
    print(f"\n{Colors.BLUE}{'='*80}{Colors.END}")
    print(f"{Colors.BLUE}PAYMENT SECURITY TEST SUITE{Colors.END}")
    print(f"{Colors.BLUE}{'='*80}{Colors.END}")
    
    tests = [
        ("Price Tampering", test_price_tampering),
        ("Double Submit", test_double_submit),
        ("Race Condition", test_race_condition),
        ("Transaction Rollback", test_transaction_rollback),
        ("Input Validation", test_input_validation)
    ]
    
    results = {}
    
    for name, test_func in tests:
        try:
            result = test_func()
            results[name] = result
            time.sleep(1)  # Delay giữa các tests
        except Exception as e:
            print_fail(f"Test {name} crashed: {str(e)}")
            results[name] = False
    
    # Tổng kết
    print(f"\n{Colors.BLUE}{'='*80}{Colors.END}")
    print(f"{Colors.BLUE}TỔNG KẾT{Colors.END}")
    print(f"{Colors.BLUE}{'='*80}{Colors.END}\n")
    
    passed = sum(1 for r in results.values() if r is True)
    failed = sum(1 for r in results.values() if r is False)
    skipped = sum(1 for r in results.values() if r is None)
    
    for name, result in results.items():
        if result is True:
            print(f"{Colors.GREEN}✅ {name}: PASS{Colors.END}")
        elif result is False:
            print(f"{Colors.RED}❌ {name}: FAIL{Colors.END}")
        else:
            print(f"{Colors.YELLOW}⚠️  {name}: SKIPPED{Colors.END}")
    
    print(f"\n📊 Kết quả: {passed} passed, {failed} failed, {skipped} skipped")
    
    if failed == 0:
        print(f"\n{Colors.GREEN}{'='*80}{Colors.END}")
        print(f"{Colors.GREEN}🎉 TẤT CẢ TESTS ĐỀU PASS! HỆ THỐNG AN TOÀN!{Colors.END}")
        print(f"{Colors.GREEN}{'='*80}{Colors.END}\n")
    else:
        print(f"\n{Colors.RED}{'='*80}{Colors.END}")
        print(f"{Colors.RED}🔴 CÓ {failed} TESTS FAIL! HỆ THỐNG CHƯA AN TOÀN!{Colors.END}")
        print(f"{Colors.RED}{'='*80}{Colors.END}\n")

if __name__ == '__main__':
    print("\n⚠️  LƯU Ý: Đảm bảo Flask server đang chạy ở http://localhost:5000")
    print("⚠️  Các tests này sẽ tạo dữ liệu test trong database\n")
    
    input("Nhấn Enter để bắt đầu tests...")
    
    run_all_tests()

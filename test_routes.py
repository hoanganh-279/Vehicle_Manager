# =============================================================================
# test_routes.py — Script test các route bị lỗi
# =============================================================================

import requests
import sys

BASE_URL = "http://localhost:5000"

def test_route(url, description):
    """Test một route và in kết quả"""
    full_url = f"{BASE_URL}{url}"
    print(f"\n{'='*70}")
    print(f"TEST: {description}")
    print(f"URL: {full_url}")
    print(f"{'='*70}")
    
    try:
        response = requests.get(full_url, timeout=5, allow_redirects=False)
        
        if response.status_code == 200:
            print(f"✅ THÀNH CÔNG - Status: {response.status_code}")
            print(f"   Content-Type: {response.headers.get('Content-Type', 'N/A')}")
            print(f"   Content-Length: {len(response.content)} bytes")
            
            # Kiểm tra có phải trang trắng không
            if len(response.content) < 100:
                print(f"   ⚠️  CẢNH BÁO: Nội dung quá ngắn, có thể là trang trắng!")
            
            # Kiểm tra encoding
            if 'charset' in response.headers.get('Content-Type', ''):
                charset = response.headers.get('Content-Type').split('charset=')[-1]
                print(f"   Charset: {charset}")
            
            return True
            
        elif response.status_code == 302:
            print(f"⚠️  REDIRECT - Status: {response.status_code}")
            print(f"   Location: {response.headers.get('Location', 'N/A')}")
            print(f"   (Có thể cần đăng nhập admin)")
            return True
            
        elif response.status_code == 404:
            print(f"❌ LỖI 404 - Route không tồn tại!")
            return False
            
        elif response.status_code == 500:
            print(f"❌ LỖI 500 - Lỗi server!")
            print(f"   Kiểm tra terminal để xem chi tiết lỗi")
            return False
            
        else:
            print(f"⚠️  Status: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ KHÔNG KẾT NỐI ĐƯỢC!")
        print(f"   → Kiểm tra app có đang chạy không: python app.py")
        return False
        
    except requests.exceptions.Timeout:
        print(f"❌ TIMEOUT!")
        print(f"   → Server phản hồi quá lâu")
        return False
        
    except Exception as e:
        print(f"❌ LỖI: {e}")
        return False

def main():
    print("\n" + "="*70)
    print("KIỂM TRA CÁC ROUTE BỊ LỖI - GIAI ĐOẠN 1")
    print("="*70)
    print(f"\nBase URL: {BASE_URL}")
    print("Đảm bảo app đang chạy: python app.py")
    print("\nNhấn Enter để bắt đầu test...")
    input()
    
    results = []
    
    # Test các route
    tests = [
        ("/parking", "Trang Xe Vào Bãi (đã bị trắng)"),
        ("/parking/exit", "Trang Xe Ra Bãi"),
        ("/admin/login", "Trang đăng nhập Admin"),
        ("/admin/dashboard", "Dashboard Admin (cần login)"),
        ("/admin/cards", "Quản lý thẻ (cần login)"),
        ("/admin/vehicles", "Quản lý xe (cần login)"),
    ]
    
    for url, desc in tests:
        result = test_route(url, desc)
        results.append((desc, result))
    
    # Tổng kết
    print("\n" + "="*70)
    print("KẾT QUẢ TỔNG HỢP")
    print("="*70)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for desc, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {desc}")
    
    print(f"\n{'='*70}")
    print(f"Tổng: {passed}/{total} routes hoạt động")
    print(f"{'='*70}")
    
    if passed == total:
        print("\n🎉 TẤT CẢ ROUTES HOẠT ĐỘNG TỐT!")
    else:
        print(f"\n⚠️  CÒN {total - passed} ROUTES BỊ LỖI")
        print("\nKiểm tra:")
        print("1. App có đang chạy không?")
        print("2. Xem log trong terminal khi chạy app")
        print("3. Kiểm tra database connection")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Đã hủy test")
        sys.exit(0)

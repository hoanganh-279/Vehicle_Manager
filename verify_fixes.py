#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
verify_fixes.py - Kiểm tra các lỗi đã được sửa trong Giai đoạn 1
"""

import os
import re

print("=" * 70)
print("KIỂM TRA CÁC LỖI ĐÃ ĐƯỢC SỬA - GIAI ĐOẠN 1")
print("=" * 70)
print()

# Màu sắc cho terminal
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def check_file_exists(filepath):
    """Kiểm tra file có tồn tại không"""
    return os.path.exists(filepath)

def check_content_in_file(filepath, pattern, description):
    """Kiểm tra nội dung trong file"""
    if not check_file_exists(filepath):
        print(f"{RED}✗{RESET} File không tồn tại: {filepath}")
        return False
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        if re.search(pattern, content):
            print(f"{GREEN}✓{RESET} {description}")
            return True
        else:
            print(f"{RED}✗{RESET} {description}")
            return False

# ============================================================================
# KIỂM TRA 1: Lỗi nút "Xem" Top 5 thẻ
# ============================================================================
print("[1] Kiểm tra lỗi nút 'Xem' Top 5 thẻ...")
print("-" * 70)

check1 = check_content_in_file(
    'admin/cards.html',
    r"url_for\('admin_card_detail',\s*card_id=card\.id\)",
    "Link 'Xem' đã dùng url_for() với card_id đầy đủ"
)

check2 = not check_content_in_file(
    'admin/cards.html',
    r'href="/admin/cards/\{\{\s*card\.id\[:8\]\s*\}\}"',
    "Không còn dùng card.id[:8] trong href (đã sửa)"
)

if check1 and check2:
    print(f"{GREEN}✅ LỖI 1: ĐÃ SỬA XONG{RESET}")
else:
    print(f"{RED}❌ LỖI 1: CHƯA SỬA XONG{RESET}")

print()

# ============================================================================
# KIỂM TRA 2: Lỗi trang /parking trắng
# ============================================================================
print("[2] Kiểm tra trang /parking...")
print("-" * 70)

check3 = check_file_exists('parking/entry.html')
if check3:
    print(f"{GREEN}✓{RESET} File parking/entry.html tồn tại")
else:
    print(f"{RED}✗{RESET} File parking/entry.html không tồn tại")

check4 = check_file_exists('base.html')
if check4:
    print(f"{GREEN}✓{RESET} File base.html tồn tại")
else:
    print(f"{RED}✗{RESET} File base.html không tồn tại")

check5 = check_content_in_file(
    'base.html',
    r'<meta charset="UTF-8">',
    "Meta charset UTF-8 đã có trong base.html"
)

check6 = check_content_in_file(
    'app.py',
    r"@app\.route\('/parking',\s*methods=\['GET',\s*'POST'\]\)",
    "Route /parking đã có trong app.py"
)

if check3 and check4 and check5 and check6:
    print(f"{GREEN}✅ LỖI 2: CẤU TRÚC ĐÚNG (Cần test trên browser){RESET}")
else:
    print(f"{RED}❌ LỖI 2: THIẾU FILE HOẶC ROUTE{RESET}")

print()

# ============================================================================
# KIỂM TRA 3: Lỗi encoding tiếng Việt
# ============================================================================
print("[3] Kiểm tra encoding tiếng Việt...")
print("-" * 70)

check7 = check_content_in_file(
    'app.py',
    r"conn\.setdecoding\(pyodbc\.SQL_WCHAR,\s*encoding='utf-16-le'\)",
    "Connection đã set decoding UTF-16LE"
)

check8 = check_content_in_file(
    'app.py',
    r"conn\.setencoding\(encoding='utf-16-le'\)",
    "Connection đã set encoding UTF-16LE"
)

if check7 and check8:
    print(f"{GREEN}✅ LỖI 3: ENCODING ĐÃ CẤU HÌNH ĐÚNG{RESET}")
    print(f"{YELLOW}⚠️  Lưu ý: Cần kiểm tra database có dùng NVARCHAR không{RESET}")
else:
    print(f"{RED}❌ LỖI 3: ENCODING CHƯA CẤU HÌNH ĐÚNG{RESET}")

print()

# ============================================================================
# KIỂM TRA 4: Lỗi lệch Port MoMo
# ============================================================================
print("[4] Kiểm tra config Port MoMo...")
print("-" * 70)

check9 = check_content_in_file(
    'app.py',
    r"app\.run\(.*port=5000",
    "App chạy ở port 5000"
)

check10 = check_file_exists('.env')
if check10:
    print(f"{GREEN}✓{RESET} File .env tồn tại")
    with open('.env', 'r', encoding='utf-8') as f:
        env_content = f.read()
        if 'localhost:5000' in env_content:
            print(f"{GREEN}✓{RESET} Config MoMo dùng port 5000")
            check11 = True
        else:
            print(f"{YELLOW}⚠️{RESET}  Config MoMo có thể dùng port khác")
            check11 = False
else:
    print(f"{RED}✗{RESET} File .env không tồn tại")
    check11 = False

if check9 and check11:
    print(f"{GREEN}✅ LỖI 4: PORT ĐÃ ĐỒNG BỘ{RESET}")
else:
    print(f"{YELLOW}⚠️  LỖI 4: CẦN KIỂM TRA PORT{RESET}")

print()

# ============================================================================
# KIỂM TRA CÁC FILE CÔNG CỤ
# ============================================================================
print("[5] Kiểm tra các file công cụ đã tạo...")
print("-" * 70)

tools = [
    'fix_encoding_complete.py',
    'fix_database_encoding.sql',
    'test_routes.py',
    'HUONG_DAN_SUA_LOI_GIAI_DOAN_1.md',
    'README_GIAI_DOAN_1.md',
    'QUICK_START_GIAI_DOAN_1.txt',
    'CHANGELOG_GIAI_DOAN_1.md'
]

all_tools_exist = True
for tool in tools:
    if check_file_exists(tool):
        print(f"{GREEN}✓{RESET} {tool}")
    else:
        print(f"{RED}✗{RESET} {tool}")
        all_tools_exist = False

if all_tools_exist:
    print(f"{GREEN}✅ TẤT CẢ FILE CÔNG CỤ ĐÃ TẠO{RESET}")
else:
    print(f"{RED}❌ THIẾU MỘT SỐ FILE CÔNG CỤ{RESET}")

print()

# ============================================================================
# TỔNG KẾT
# ============================================================================
print("=" * 70)
print("TỔNG KẾT GIAI ĐOẠN 1")
print("=" * 70)
print()

results = [
    ("Lỗi nút 'Xem' Top 5 thẻ", check1 and check2),
    ("Lỗi trang /parking trắng", check3 and check4 and check5 and check6),
    ("Lỗi encoding tiếng Việt", check7 and check8),
    ("Lỗi lệch Port MoMo", check9 and check11),
    ("Các file công cụ", all_tools_exist)
]

passed = sum(1 for _, status in results if status)
total = len(results)

for name, status in results:
    if status:
        print(f"{GREEN}✅{RESET} {name}")
    else:
        print(f"{RED}❌{RESET} {name}")

print()
print(f"Kết quả: {passed}/{total} mục đã hoàn thành")
print()

if passed == total:
    print(f"{GREEN}🎉 GIAI ĐOẠN 1 ĐÃ HOÀN THÀNH!{RESET}")
    print()
    print("Bước tiếp theo:")
    print("1. Chạy app: python app.py")
    print("2. Test trên browser:")
    print("   - http://localhost:5000/parking")
    print("   - http://localhost:5000/admin/cards")
    print("3. Kiểm tra font chữ tiếng Việt có hiển thị đúng không")
else:
    print(f"{YELLOW}⚠️  GIAI ĐOẠN 1 CHƯA HOÀN THÀNH{RESET}")
    print()
    print("Cần làm:")
    for name, status in results:
        if not status:
            print(f"  - Sửa: {name}")

print()
print("=" * 70)

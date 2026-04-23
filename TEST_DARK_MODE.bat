@echo off
chcp 65001 >nul
echo.
echo ╔══════════════════════════════════════════════════════════════════╗
echo ║          🌙 TEST DARK MODE - QUICK CHECK                         ║
echo ╚══════════════════════════════════════════════════════════════════╝
echo.
echo ✅ Đang kiểm tra các file...
echo.

REM Kiểm tra file CSS
if exist "static\css\dark-mode-fix.css" (
    echo [✓] dark-mode-fix.css - OK
) else (
    echo [✗] dark-mode-fix.css - MISSING
)

REM Kiểm tra file JS
if exist "static\js\chart-theme.js" (
    echo [✓] chart-theme.js - OK
) else (
    echo [✗] chart-theme.js - MISSING
)

REM Kiểm tra file demo
if exist "DEMO_DARK_MODE_FIX.html" (
    echo [✓] DEMO_DARK_MODE_FIX.html - OK
) else (
    echo [✗] DEMO_DARK_MODE_FIX.html - MISSING
)

echo.
echo ══════════════════════════════════════════════════════════════════
echo.
echo 📋 HƯỚNG DẪN TEST:
echo.
echo 1. Mở Demo:
echo    - Double-click file: DEMO_DARK_MODE_FIX.html
echo    - Click nút "Dark Mode" ở góc phải trên
echo    - Kiểm tra tất cả components
echo.
echo 2. Test trên hệ thống thật:
echo    - Chạy Flask app: python app.py
echo    - Mở: http://localhost:5000/admin/dashboard
echo    - Click nút toggle Dark/Light mode
echo.
echo 3. Kiểm tra:
echo    ✓ Input có nền tối không?
echo    ✓ Card có viền mỏng không?
echo    ✓ Biểu đồ đổi màu lưới không?
echo    ✓ Chữ có đủ sáng để đọc không?
echo.
echo ══════════════════════════════════════════════════════════════════
echo.
echo 🚀 Mở Demo ngay bây giờ? (Y/N)
set /p choice="Nhập lựa chọn: "

if /i "%choice%"=="Y" (
    echo.
    echo Đang mở demo...
    start DEMO_DARK_MODE_FIX.html
    echo ✅ Demo đã được mở trong browser!
) else (
    echo.
    echo Bạn có thể mở demo sau bằng cách double-click file:
    echo DEMO_DARK_MODE_FIX.html
)

echo.
echo ══════════════════════════════════════════════════════════════════
echo.
echo 📚 Đọc hướng dẫn chi tiết:
echo    - HUONG_DAN_DARK_MODE_FIX.md
echo    - QUICK_START_DARK_MODE.txt
echo    - BEFORE_AFTER_DARK_MODE.md
echo.
pause

# =============================================================================
# app.py — Hệ Thống Quản Lý Bãi Xe NQT
# =============================================================================
# Cấu trúc thư mục:
#   E:\Quan_Ly_Bai_Xe\
#   ├── app.py
#   ├── templates\
#   │   ├── admin_base.html
#   │   ├── admin\
#   │   │   ├── login.html
#   │   │   ├── dashboard.html
#   │   │   ├── pricing.html
#   │   │   ├── revenue.html
#   │   │   ├── transactions.html
#   │   │   ├── vehicles.html
#   │   │   ├── cards.html
#   │   │   ├── card\
#   │   │   │   ├── detail.html
#   │   │   │   └── topup\history.html
#   │   │   ├── invoice\
#   │   │   │   ├── detail.html
#   │   │   │   ├── pdf_template.html
#   │   │   │   └── email_template.html
#   │   │   └── parking\spaces.html
#   │   ├── auto\entry.html
#   │   ├── card\
#   │   │   ├── register.html
#   │   │   └── topup.html
#   │   ├── kiosk\payment.html
#   │   ├── license\plate.html
#   │   ├── parking\
#   │   │   ├── entry.html
#   │   │   └── exit.html
#   │   └── payment\result.html
#   └── static\
#       └── uploads\
# =============================================================================

import os
import io
import json
import sqlite3
import pdfkit
from datetime import datetime, timedelta, date
from functools import wraps

from flask import (
    Flask, render_template, request, redirect,
    url_for, session, jsonify, Response, flash,
    send_file
)
from flask_mail import Mail, Message

# =============================================================================
# KHỞI TẠO APP
# =============================================================================

app = Flask(__name__)
app.secret_key = 'nqt_parking_secret_key_2025'  # ⚠️ Đổi thành key bí mật thật

# =============================================================================
# CẤU HÌNH DATABASE
# =============================================================================

DATABASE = 'parking.db'  # Đường dẫn file SQLite

def get_db():
    """Tạo kết nối tới database."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def query_db(query, args=(), one=False):
    """Truy vấn database, trả về list hoặc một row."""
    conn = get_db()
    cur = conn.execute(query, args)
    rv = cur.fetchall()
    conn.close()
    return (rv[0] if rv else None) if one else rv

def execute_db(query, args=()):
    """Thực thi INSERT/UPDATE/DELETE."""
    conn = get_db()
    cur = conn.execute(query, args)
    conn.commit()
    last_id = cur.lastrowid
    conn.close()
    return last_id

# =============================================================================
# CẤU HÌNH pdfkit (wkhtmltopdf)
# =============================================================================

PDFKIT_CONFIG = pdfkit.configuration(
    wkhtmltopdf=r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
)

PDFKIT_OPTIONS = {
    'page-size': 'A4',
    'encoding': 'UTF-8',
    'no-outline': None,
    'quiet': '',
}

# =============================================================================
# CẤU HÌNH FLASK-MAIL (Gmail)
# =============================================================================

app.config['MAIL_SERVER']         = 'smtp.gmail.com'
app.config['MAIL_PORT']           = 587
app.config['MAIL_USE_TLS']        = True
app.config['MAIL_USERNAME']       = 'your_email@gmail.com'       # ⚠️ Đổi email thật
app.config['MAIL_PASSWORD']       = 'your_gmail_app_password'    # ⚠️ Dùng App Password
app.config['MAIL_DEFAULT_SENDER'] = ('Bãi Xe NQT', 'your_email@gmail.com')

mail = Mail(app)

# =============================================================================
# TEMPLATE FILTER
# =============================================================================

@app.template_filter('format_currency')
def format_currency(value):
    """Filter định dạng tiền tệ: 500000 → 500,000"""
    try:
        return f"{int(value):,}"
    except (ValueError, TypeError):
        return value

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def format_amount(amount):
    """Định dạng số tiền: 500000 → '500,000 đ'"""
    try:
        return f"{int(amount):,} đ"
    except (ValueError, TypeError):
        return f"{amount} đ"

def get_invoice_number(transaction_id):
    """Tạo số hóa đơn từ ID giao dịch."""
    return f"HD-{transaction_id:06d}"

def get_status_text(status):
    """Chuyển status tiếng Anh sang tiếng Việt."""
    mapping = {
        'completed': 'Hoàn thành',
        'pending':   'Đang chờ',
        'failed':    'Thất bại',
    }
    return mapping.get(str(status).lower(), status)

def get_date_range(date_range, start_date_str=None, end_date_str=None):
    """Tính toán khoảng ngày theo bộ lọc."""
    today = date.today()
    if date_range == 'today':
        return str(today), str(today)
    elif date_range == 'week':
        return str(today - timedelta(days=7)), str(today)
    elif date_range == 'month':
        return str(today - timedelta(days=30)), str(today)
    elif date_range == 'custom' and start_date_str and end_date_str:
        return start_date_str, end_date_str
    else:  # 'all'
        return '2000-01-01', str(today)

# =============================================================================
# DECORATOR XÁC THỰC ADMIN
# =============================================================================

def login_required(f):
    """Kiểm tra đăng nhập admin trước khi vào route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# =============================================================================
# ── ADMIN: ĐĂNG NHẬP / ĐĂNG XUẤT ──
# =============================================================================

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """
    GET : Hiển thị form đăng nhập
    POST: Xử lý đăng nhập
    Template: templates/admin/login.html
    """
    if request.method == 'POST':
        email    = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        # TODO: Thay bằng truy vấn DB thực tế
        # admin = query_db('SELECT * FROM admins WHERE email=?', [email], one=True)
        # if admin and check_password_hash(admin['password'], password):
        if email == 'admin@nqt.com' and password == 'admin123':
            session['admin_logged_in'] = True
            session['admin_email']     = email
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Email hoặc mật khẩu không đúng!', 'error')

    return render_template('admin/login.html')


@app.route('/admin/logout')
def admin_logout():
    """Xóa session và chuyển về trang đăng nhập."""
    session.clear()
    return redirect(url_for('admin_login'))


@app.route('/admin')
@app.route('/')
def index():
    """Trang gốc → chuyển về dashboard hoặc login."""
    if 'admin_logged_in' in session:
        return redirect(url_for('admin_dashboard'))
    return redirect(url_for('admin_login'))

# =============================================================================
# ── ADMIN: DASHBOARD ──
# =============================================================================

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    """
    Trang tổng quan với thống kê doanh thu hôm nay.
    Template: templates/admin/dashboard.html
    Biến: daily_revenue, motorbike_revenue, car_revenue,
          hourly_entries_by_type, hourly_exits_by_type
    """
    today = str(date.today())

    # TODO: Thay bằng truy vấn DB thực tế
    daily_revenue      = 0
    motorbike_revenue  = 0
    car_revenue        = 0
    hourly_entries_by_type = {}
    hourly_exits_by_type   = {}

    return render_template(
        'admin/dashboard.html',
        daily_revenue           = daily_revenue,
        motorbike_revenue       = motorbike_revenue,
        car_revenue             = car_revenue,
        hourly_entries_by_type  = hourly_entries_by_type,
        hourly_exits_by_type    = hourly_exits_by_type,
    )

# =============================================================================
# ── ADMIN: BẢNG GIÁ ──
# =============================================================================

@app.route('/admin/pricing')
@login_required
def admin_pricing():
    """
    Hiển thị bảng giá hiện tại.
    Template: templates/admin/pricing.html (hoặc pricing/management.html)
    Biến: prices (list of tuples)
    """
    prices = query_db('SELECT * FROM pricing ORDER BY id')
    return render_template('admin/pricing.html', prices=prices)


@app.route('/admin/pricing/update', methods=['POST'])
@login_required
def admin_pricing_update():
    """
    API cập nhật giá (gọi từ fetch trong template).
    Body: id, price_per_hour
    """
    price_id      = request.form.get('id')
    price_per_hour = request.form.get('price_per_hour')

    if not price_id or not price_per_hour:
        return jsonify({'success': False, 'message': 'Thiếu thông tin'})

    try:
        execute_db(
            'UPDATE pricing SET price_per_hour=? WHERE id=?',
            [float(price_per_hour), int(price_id)]
        )
        return jsonify({'success': True, 'message': 'Cập nhật giá thành công'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# =============================================================================
# ── ADMIN: DOANH THU ──
# =============================================================================

@app.route('/admin/revenue')
@login_required
def admin_revenue():
    """
    Thống kê doanh thu theo khoảng thời gian.
    Template: templates/admin/revenue.html
    Params: date_range, start_date, end_date
    Biến: daily_revenue (list), total_revenue, card_revenue,
          momo_revenue, stripe_revenue, vnpay_revenue,
          total_motorbike_revenue, total_car_revenue,
          total_transactions, start_date, end_date, date_range
    """
    date_range     = request.args.get('date_range', 'week')
    start_date_str = request.args.get('start_date')
    end_date_str   = request.args.get('end_date')
    start_date, end_date = get_date_range(date_range, start_date_str, end_date_str)

    # TODO: Thay bằng truy vấn DB thực tế
    daily_revenue          = []
    total_revenue          = 0
    card_revenue           = 0
    momo_revenue           = 0
    stripe_revenue         = 0
    vnpay_revenue          = 0
    total_motorbike_revenue = 0
    total_car_revenue       = 0
    total_transactions      = 0

    return render_template(
        'admin/revenue.html',
        daily_revenue           = daily_revenue,
        total_revenue           = total_revenue,
        card_revenue            = card_revenue,
        momo_revenue            = momo_revenue,
        stripe_revenue          = stripe_revenue,
        vnpay_revenue           = vnpay_revenue,
        total_motorbike_revenue = total_motorbike_revenue,
        total_car_revenue       = total_car_revenue,
        total_transactions      = total_transactions,
        start_date              = start_date,
        end_date                = end_date,
        date_range              = date_range,
    )


@app.route('/admin/export_revenue_excel')
@login_required
def export_revenue_excel():
    """Xuất báo cáo doanh thu ra file Excel."""
    # TODO: Dùng openpyxl hoặc xlsxwriter
    return jsonify({'message': 'Chức năng đang phát triển'})


@app.route('/admin/export_revenue_pdf')
@login_required
def export_revenue_pdf():
    """Xuất báo cáo doanh thu ra file PDF."""
    # TODO: Dùng pdfkit
    return jsonify({'message': 'Chức năng đang phát triển'})

# =============================================================================
# ── ADMIN: GIAO DỊCH ──
# =============================================================================

@app.route('/admin/transactions')
@login_required
def admin_transactions():
    """
    Danh sách tất cả giao dịch (đỗ xe).
    Template: templates/admin/transactions.html
    Params: date_range, transaction_type, status, start_date, end_date
    Biến: transactions (list), daily_data, date_range,
          transaction_type, status, start_date, end_date
    """
    date_range       = request.args.get('date_range', 'week')
    transaction_type = request.args.get('transaction_type', '')
    status           = request.args.get('status', '')
    start_date_str   = request.args.get('start_date')
    end_date_str     = request.args.get('end_date')
    start_date, end_date = get_date_range(date_range, start_date_str, end_date_str)

    # TODO: Thay bằng truy vấn DB thực tế
    transactions = []
    daily_data   = []

    return render_template(
        'admin/transactions.html',
        transactions     = transactions,
        daily_data       = daily_data,
        date_range       = date_range,
        transaction_type = transaction_type,
        status           = status,
        start_date       = start_date,
        end_date         = end_date,
    )


@app.route('/admin/export_transactions_excel')
@login_required
def export_transactions_excel():
    """Xuất danh sách giao dịch ra Excel."""
    # TODO: Dùng openpyxl
    return jsonify({'message': 'Chức năng đang phát triển'})

# =============================================================================
# ── ADMIN: XE ──
# =============================================================================

@app.route('/admin/vehicles')
@login_required
def admin_vehicles():
    """
    Danh sách xe đang đỗ và lịch sử xe.
    Template: templates/admin/vehicles.html
    """
    # TODO: Truy vấn DB
    parked_vehicles  = []
    history_vehicles = []
    return render_template(
        'admin/vehicles.html',
        parked_vehicles  = parked_vehicles,
        history_vehicles = history_vehicles,
    )


@app.route('/admin/vehicles/<int:vehicle_id>')
@login_required
def admin_vehicle_detail(vehicle_id):
    """
    Chi tiết một xe cụ thể.
    Template: templates/admin/vehicle/detail.html
    Biến: vehicle (object với các thuộc tính:
          id, license_plate, plate_color, vehicle_type, plate_type,
          status, entry_time, exit_time, duration,
          estimated_fee, actual_fee,
          face_image_path, plate_image_path, qr_code_path,
          exit_face_image_path, exit_plate_image_path)
    """
    vehicle = query_db('SELECT * FROM vehicles WHERE id=?', [vehicle_id], one=True)
    if not vehicle:
        flash('Không tìm thấy xe!', 'error')
        return redirect(url_for('admin_vehicles'))
    return render_template('admin/vehicle/detail.html', vehicle=vehicle)


@app.route('/admin/vehicles/force_exit/<int:vehicle_id>', methods=['POST'])
@login_required
def admin_vehicle_force_exit(vehicle_id):
    """API ép buộc xe ra bãi."""
    try:
        # TODO: Tính phí và cập nhật DB
        parking_fee = 0
        execute_db(
            'UPDATE vehicles SET status=?, exit_time=? WHERE id=?',
            ['exited', datetime.now(), vehicle_id]
        )
        return jsonify({
            'success': True,
            'message': f'Đã ép xe ra bãi thành công',
            'parking_fee': parking_fee
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/admin/vehicles/delete/<int:vehicle_id>', methods=['POST'])
@login_required
def admin_vehicle_delete(vehicle_id):
    """API xóa xe khỏi hệ thống."""
    try:
        execute_db('DELETE FROM vehicles WHERE id=?', [vehicle_id])
        return jsonify({'success': True, 'message': 'Đã xóa xe thành công'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# =============================================================================
# ── ADMIN: THẺ XE ──
# =============================================================================

@app.route('/admin/cards')
@login_required
def admin_cards():
    """
    Danh sách tất cả thẻ xe.
    Template: templates/admin/cards.html
    Biến: cards (list), daily_registrations, daily_topups
    """
    cards               = query_db('SELECT * FROM cards ORDER BY created_at DESC')
    daily_registrations = []  # TODO: Truy vấn DB
    daily_topups        = []  # TODO: Truy vấn DB
    return render_template(
        'admin/cards.html',
        cards               = cards,
        daily_registrations = daily_registrations,
        daily_topups        = daily_topups,
    )


@app.route('/admin/cards/<card_id>')
@login_required
def admin_card_detail(card_id):
    """
    Chi tiết một thẻ xe.
    Template: templates/admin/card/detail.html
    Biến: card (object)
    """
    card = query_db('SELECT * FROM cards WHERE id=?', [card_id], one=True)
    if not card:
        flash('Không tìm thấy thẻ!', 'error')
        return redirect(url_for('admin_cards'))
    return render_template('admin/card/detail.html', card=card)


@app.route('/admin/cards/delete/<card_id>', methods=['POST'])
@login_required
def admin_card_delete(card_id):
    """API xóa thẻ xe."""
    try:
        execute_db('DELETE FROM cards WHERE id=?', [card_id])
        return jsonify({'success': True, 'message': 'Đã xóa thẻ thành công'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# =============================================================================
# ── ADMIN: LỊCH SỬ NẠP TIỀN THẺ ──
# =============================================================================

@app.route('/admin/card/topup/history')
@login_required
def admin_card_topup_history():
    """
    Lịch sử nạp tiền thẻ xe.
    Template: templates/admin/card/topup/history.html
    Params: date_range, start_date, end_date
    Biến: topup_history (list of records), total_successful,
          total_amount, date_list, daily_counts,
          start_date, end_date, date_range
    """
    date_range     = request.args.get('date_range', 'week')
    start_date_str = request.args.get('start_date')
    end_date_str   = request.args.get('end_date')
    start_date, end_date = get_date_range(date_range, start_date_str, end_date_str)

    # TODO: Truy vấn DB — mỗi record cần có các thuộc tính:
    # id, card_id, name, phone, amount, payment_method,
    # transaction_id, status, created_at
    topup_history    = []
    total_successful = 0
    total_amount     = 0
    date_list        = []
    daily_counts     = []

    return render_template(
        'admin/card/topup/history.html',
        topup_history    = topup_history,
        total_successful = total_successful,
        total_amount     = total_amount,
        date_list        = date_list,
        daily_counts     = daily_counts,
        start_date       = start_date,
        end_date         = end_date,
        date_range       = date_range,
    )


@app.route('/admin/card/topup/export-excel')
@login_required
def export_topup_excel():
    """Xuất lịch sử nạp tiền ra file Excel."""
    # TODO: Dùng openpyxl
    return jsonify({'message': 'Chức năng đang phát triển'})

# =============================================================================
# ── ADMIN: HÓA ĐƠN ──
# =============================================================================

@app.route('/admin/invoice/<int:transaction_id>')
@login_required
def admin_invoice_detail(transaction_id):
    """
    Xem chi tiết hóa đơn giao dịch nạp tiền.
    Template: templates/admin/invoice/detail.html
    Biến: transaction (tuple), invoice_number, amount_formatted,
          status_text, now
    transaction tuple:
      [0]=id, [1]=card_id, [2]=name, [3]=phone, [4]=email,
      [5]=amount, [6]=payment_method, [7]=transaction_id,
      [8]=status, [9]=created_at (datetime)
    """
    transaction = query_db(
        '''SELECT t.id, t.card_id, c.name, c.phone, c.email,
                  t.amount, t.payment_method, t.transaction_id,
                  t.status, t.created_at
           FROM topup_transactions t
           LEFT JOIN cards c ON t.card_id = c.id
           WHERE t.id = ?''',
        [transaction_id], one=True
    )

    if not transaction:
        flash('Không tìm thấy giao dịch!', 'error')
        return redirect(url_for('admin_card_topup_history'))

    return render_template(
        'admin/invoice/detail.html',
        transaction      = transaction,
        invoice_number   = get_invoice_number(transaction[0]),
        amount_formatted = format_amount(transaction[5]),
        status_text      = get_status_text(transaction[8]),
        now              = datetime.now(),
    )


@app.route('/admin/invoice/export/<int:transaction_id>')
@login_required
def export_invoice(transaction_id):
    """
    Xuất hóa đơn ra file PDF dùng pdfkit.
    Template: templates/admin/invoice/pdf_template.html
    """
    transaction = query_db(
        '''SELECT t.id, t.card_id, c.name, c.phone, c.email,
                  t.amount, t.payment_method, t.transaction_id,
                  t.status, t.created_at
           FROM topup_transactions t
           LEFT JOIN cards c ON t.card_id = c.id
           WHERE t.id = ?''',
        [transaction_id], one=True
    )

    if not transaction:
        return jsonify({'error': 'Không tìm thấy giao dịch'}), 404

    invoice_number = get_invoice_number(transaction[0])

    html = render_template(
        'admin/invoice/pdf_template.html',
        transaction      = transaction,
        invoice_number   = invoice_number,
        amount_formatted = format_amount(transaction[5]),
        status_text      = get_status_text(transaction[8]),
        now              = datetime.now(),
    )

    try:
        pdf = pdfkit.from_string(
            html, False,
            configuration = PDFKIT_CONFIG,
            options       = PDFKIT_OPTIONS
        )
        return Response(
            pdf,
            mimetype = 'application/pdf',
            headers  = {
                'Content-Disposition':
                    f'attachment; filename=HoaDon_{invoice_number}.pdf'
            }
        )
    except Exception as e:
        return jsonify({'error': f'Lỗi xuất PDF: {str(e)}'}), 500


@app.route('/admin/invoice/send-email/<int:transaction_id>')
@login_required
def send_invoice_email(transaction_id):
    """
    Gửi hóa đơn qua email cho khách hàng dùng flask-mail.
    Template: templates/admin/invoice/email_template.html
    """
    transaction = query_db(
        '''SELECT t.id, t.card_id, c.name, c.phone, c.email,
                  t.amount, t.payment_method, t.transaction_id,
                  t.status, t.created_at
           FROM topup_transactions t
           LEFT JOIN cards c ON t.card_id = c.id
           WHERE t.id = ?''',
        [transaction_id], one=True
    )

    if not transaction:
        flash('Không tìm thấy giao dịch!', 'error')
        return redirect(url_for('admin_card_topup_history'))

    customer_email = transaction[4]  # transaction[4] = email
    if not customer_email:
        flash('Khách hàng không có email!', 'error')
        return redirect(url_for('admin_invoice_detail', transaction_id=transaction_id))

    invoice_number = get_invoice_number(transaction[0])

    html_body = render_template(
        'admin/invoice/email_template.html',
        transaction      = transaction,
        invoice_number   = invoice_number,
        amount_formatted = format_amount(transaction[5]),
        status_text      = get_status_text(transaction[8]),
        now              = datetime.now(),
    )

    try:
        msg = Message(
            subject    = f'Xác nhận giao dịch {invoice_number} — Bãi Xe NQT',
            recipients = [customer_email],
            html       = html_body,
        )
        mail.send(msg)
        flash(f'Đã gửi hóa đơn tới {customer_email} thành công!', 'success')
    except Exception as e:
        flash(f'Lỗi gửi email: {str(e)}', 'error')

    return redirect(url_for('admin_invoice_detail', transaction_id=transaction_id))

# =============================================================================
# ── ADMIN: SƠ ĐỒ BÃI ĐỖ ──
# =============================================================================

@app.route('/admin/parking_spaces')
@login_required
def admin_parking_spaces():
    """
    Sơ đồ và cấu hình bãi đỗ xe.
    Template: templates/admin/parking/spaces.html
    """
    # TODO: Truy vấn DB
    return render_template('admin/parking/spaces.html')


@app.route('/admin/parking_spaces/update_config', methods=['POST'])
@login_required
def admin_parking_spaces_update_config():
    """API cập nhật cấu hình bãi đỗ."""
    # TODO: Xử lý logic
    return jsonify({'success': True})


@app.route('/admin/parking_spaces/api/realtime')
@login_required
def admin_parking_spaces_realtime():
    """API lấy dữ liệu thời gian thực cho sơ đồ bãi."""
    # TODO: Truy vấn DB
    return jsonify({'spaces': []})


@app.route('/admin/parking_spaces/vehicle/<int:vehicle_id>')
@login_required
def admin_parking_spaces_vehicle(vehicle_id):
    """API lấy thông tin xe trong ô đỗ."""
    vehicle = query_db('SELECT * FROM vehicles WHERE id=?', [vehicle_id], one=True)
    if vehicle:
        return jsonify(dict(vehicle))
    return jsonify({'error': 'Không tìm thấy'}), 404


@app.route('/admin/migrate_parking_spots', methods=['POST'])
@login_required
def admin_migrate_parking_spots():
    """API migrate dữ liệu ô đỗ xe."""
    # TODO: Xử lý migrate
    return jsonify({'success': True})

# =============================================================================
# ── NHẬN DIỆN BIỂN SỐ ──
# =============================================================================

@app.route('/recognize_plate', methods=['POST'])
def recognize_plate():
    """
    API nhận diện biển số xe từ ảnh upload.
    Template: templates/license/plate.html
    Input: form-data với file ảnh
    Output: JSON với thông tin biển số
    """
    if 'file' not in request.files:
        return jsonify({'error': 'Không có file'}), 400

    file = request.files['file']
    # TODO: Tích hợp model AI nhận diện biển số
    # Trả về mẫu:
    return jsonify({
        'success': True,
        'plates': [
            {
                'van_ban':       '51A-123.45',
                'mau':           'Trắng',
                'loai':          'Xe máy',
                'vehicle_type':  'motorbike',
            }
        ],
        'original_image':  '/static/uploads/original.jpg',
        'result_image':    '/static/uploads/result.jpg',
    })


@app.route('/license/plate', methods=['GET', 'POST'])
def license_plate():
    """
    Trang nhận diện biển số (dạng web thông thường).
    Template: templates/license/plate.html
    """
    if request.method == 'POST':
        if 'file' not in request.files:
            return render_template('license/plate.html', error='Vui lòng chọn file ảnh')

        file = request.files['file']
        # TODO: Lưu file và xử lý nhận diện
        return render_template(
            'license/plate.html',
            original_image = '/static/uploads/original.jpg',
            result_image   = 'static\\uploads\\result.jpg',
            plates         = [],
        )

    return render_template('license/plate.html')

# =============================================================================
# ── CỔNG VÀO BÃI (AUTO) ──
# =============================================================================

@app.route('/auto/entry')
def auto_entry():
    """
    Màn hình cổng vào tự động.
    Template: templates/auto/entry.html
    """
    return render_template('auto/entry.html')

# =============================================================================
# ── BÃI ĐỖ XE: VÀO / RA ──
# =============================================================================

@app.route('/parking')
def parking_entry_page():
    """
    Trang giao diện cho xe vào bãi.
    Template: templates/parking/entry.html
    """
    return render_template('parking/entry.html')


@app.route('/parking', methods=['POST'])
def parking_entry():
    """
    API xử lý xe vào bãi (nhận dữ liệu từ camera/form).
    Input JSON: license_plate, plate_image, face_image, card_id, ...
    """
    data = request.get_json() or {}
    # TODO: Lưu thông tin xe vào DB, tạo QR code, ...
    return jsonify({
        'success':       True,
        'message':       'Xe đã vào bãi thành công',
        'vehicle_id':    1,
        'qr_code_path':  '/static/uploads/qr.png',
    })


@app.route('/parking/exit')
def parking_exit_page():
    """
    Trang giao diện cho xe ra bãi.
    Template: templates/parking/exit.html
    """
    return render_template('parking/exit.html')


@app.route('/parking/exit', methods=['POST'])
def parking_exit():
    """
    API xử lý xe ra bãi, tính phí, thanh toán.
    Input JSON: license_plate / qr_data / card_id, payment_method, ...
    """
    data = request.get_json() or {}
    # TODO: Tính phí, tích hợp cổng thanh toán
    return jsonify({
        'success':      True,
        'message':      'Xử lý thành công',
        'parking_fee':  5000,
        'pay_url':      None,   # URL thanh toán MoMo/VNPay nếu có
        'momo_pay_url': None,
        'vnpay_pay_url':None,
    })


@app.route('/parking/topup/result', methods=['POST'])
def parking_topup_result():
    """API kiểm tra kết quả nạp tiền khi đang ở cổng ra."""
    data = request.get_json() or {}
    # TODO: Kiểm tra trạng thái giao dịch
    return jsonify({'success': True, 'balance': 0})

# =============================================================================
# ── THẺ XE ──
# =============================================================================

@app.route('/card/register', methods=['GET', 'POST'])
def card_register():
    """
    Đăng ký thẻ xe mới.
    GET : Hiển thị form đăng ký
    POST: Xử lý đăng ký (nhận face image, thông tin khách hàng)
    Template: templates/card/register.html
    """
    if request.method == 'POST':
        data = request.form.to_dict()
        # TODO: Lưu thông tin vào DB, tạo QR code
        return jsonify({
            'success':     True,
            'message':     'Đăng ký thẻ thành công',
            'card_id':     'CARD001',
            'qr_code_url': '/static/uploads/qr.png',
        })
    return render_template('card/register.html')


@app.route('/card/topup', methods=['GET', 'POST'])
def card_topup():
    """
    Nạp tiền vào thẻ xe.
    Template: templates/card/topup.html
    """
    if request.method == 'POST':
        data = request.get_json() or {}
        # TODO: Xử lý nạp tiền
        return jsonify({'success': True, 'pay_url': None})
    return render_template('card/topup.html')


@app.route('/card/info')
def card_info():
    """
    API lấy thông tin thẻ xe theo card_id.
    Params: card_id
    """
    card_id = request.args.get('card_id')
    if not card_id:
        return jsonify({'error': 'Thiếu card_id'}), 400

    card = query_db('SELECT * FROM cards WHERE id=?', [card_id], one=True)
    if card:
        return jsonify({'success': True, 'card': dict(card)})
    return jsonify({'success': False, 'error': 'Không tìm thấy thẻ'}), 404

# =============================================================================
# ── KIOSK: THANH TOÁN ──
# =============================================================================

@app.route('/kiosk/payment', methods=['GET', 'POST'])
def kiosk_payment():
    """
    Màn hình thanh toán tại kiosk.
    GET : Hiển thị trang thanh toán
    POST: Xử lý thanh toán (card/stripe/momo/vnpay)
    Template: templates/kiosk/payment.html
    """
    if request.method == 'POST':
        data = request.get_json() or {}
        payment_method = data.get('payment_method', 'card')
        # TODO: Tích hợp cổng thanh toán
        return jsonify({
            'success':  True,
            'pay_url':  None,
            'message':  'Thanh toán thành công',
        })
    return render_template('kiosk/payment.html')

# =============================================================================
# ── THANH TOÁN: KẾT QUẢ ──
# =============================================================================

@app.route('/payment/result')
def payment_result():
    """
    Trang hiển thị kết quả thanh toán (callback từ MoMo/VNPay).
    Template: templates/payment/result.html
    Biến: pay_url, message
    """
    pay_url = request.args.get('pay_url')
    message = request.args.get('message', 'Xử lý thanh toán thành công')
    return render_template('payment/result.html', pay_url=pay_url, message=message)

# =============================================================================
# ── API KIỂM TRA TRẠNG THÁI THANH TOÁN ──
# =============================================================================

@app.route('/check_momo_payment_status')
def check_momo_payment_status():
    """
    API kiểm tra trạng thái thanh toán MoMo.
    Params: qr_data, timestamp
    """
    qr_data   = request.args.get('qr_data')
    timestamp = request.args.get('timestamp')
    # TODO: Gọi API MoMo để kiểm tra
    return jsonify({'status': 'pending', 'paid': False})


@app.route('/check_vnpay_payment_status')
def check_vnpay_payment_status():
    """
    API kiểm tra trạng thái thanh toán VNPay.
    Params: qr_data, timestamp
    """
    qr_data   = request.args.get('qr_data')
    timestamp = request.args.get('timestamp')
    # TODO: Gọi API VNPay để kiểm tra
    return jsonify({'status': 'pending', 'paid': False})


@app.route('/api/mobile/check_payment_status/<int:vehicle_id>')
def check_mobile_payment_status(vehicle_id):
    """API kiểm tra trạng thái thanh toán từ mobile."""
    # TODO: Kiểm tra DB
    return jsonify({'paid': False, 'vehicle_id': vehicle_id})

# =============================================================================
# ── API LẤY THÔNG TIN XE ──
# =============================================================================

@app.route('/get_vehicle_info')
def get_vehicle_info():
    """
    API lấy thông tin xe theo biển số (QR).
    Params: license_plate
    """
    license_plate = request.args.get('license_plate')
    if not license_plate:
        return jsonify({'error': 'Thiếu biển số'}), 400

    vehicle = query_db(
        "SELECT * FROM vehicles WHERE license_plate=? AND status='parked'",
        [license_plate], one=True
    )
    if vehicle:
        return jsonify({'success': True, 'vehicle': dict(vehicle)})
    return jsonify({'success': False, 'error': 'Không tìm thấy xe'}), 404

# =============================================================================
# ── API CHATBOT ──
# =============================================================================

@app.route('/api/chatbot/ask', methods=['POST'])
def chatbot_ask():
    """API chatbot hỏi đáp (dùng trong base.html)."""
    data     = request.get_json() or {}
    question = data.get('question', '')
    # TODO: Tích hợp AI chatbot
    return jsonify({'answer': 'Chức năng chatbot đang phát triển.'})


@app.route('/api/chatbot/test')
def chatbot_test():
    """API kiểm tra chatbot còn hoạt động không."""
    return jsonify({'status': 'ok'})

# =============================================================================
# ── CHẠY APP ──
# =============================================================================

if __name__ == '__main__':
    # Tạo thư mục uploads nếu chưa có
    os.makedirs(os.path.join('static', 'uploads'), exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5000)
# Hướng Dẫn Sử Dụng Dynamic Rule-based Pricing

## Tổng quan
Hệ thống Dynamic Rule-based Pricing cho phép bạn cấu hình giá đỗ xe linh hoạt theo nhiều điều kiện khác nhau như:
- Khung giờ bình thường
- Phí qua đêm
- Ngày lễ / Sự kiện
- Phụ phí cuối tuần

## Cài đặt

### Bước 1: Tạo bảng database
Chạy file SQL để tạo bảng `pricing_rules`:

```bash
# Mở SQL Server Management Studio hoặc Azure Data Studio
# Kết nối đến database ParkingManagement
# Chạy file: create_pricing_rules_table.sql
```

Hoặc chạy trực tiếp:
```sql
sqlcmd -S LAPTOP-3J6T1I18\SQLEXPRESS01 -d ParkingManagement -i create_pricing_rules_table.sql
```

### Bước 2: Cập nhật route trong app.py
Route đã được thêm sẵn:
- `/admin/pricing/dynamic` - Trang cấu hình
- `/admin/pricing/save-dynamic` - API lưu cấu hình

### Bước 3: Truy cập trang mới
Mở trình duyệt và truy cập:
```
http://localhost:5000/admin/pricing/dynamic
```

## Cách sử dụng

### 1. Thêm cấu hình mới

#### Bước 1: Chọn loại xe
- Click tab "Xe máy" hoặc "Xe hơi"

#### Bước 2: Thêm cấu hình
- Click nút "**+ Thêm cấu hình mới**"
- Một card cấu hình mới sẽ xuất hiện

#### Bước 3: Điền thông tin

**Loại cấu hình:**
- **Khung giờ bình thường**: Giá theo khung giờ trong ngày
- **Phí qua đêm**: Phí cố định cho xe qua đêm
- **Ngày lễ / Sự kiện**: Giá đặc biệt cho ngày lễ
- **Phụ phí cuối tuần**: Phí thêm cho cuối tuần

**Tên cấu hình:**
- VD: "Giá xe máy ban ngày", "Phí Tết Nguyên Đán"

**Điều kiện thời gian:**
- Với "Khung giờ" hoặc "Cuối tuần": Chọn giờ bắt đầu - giờ kết thúc
- Với "Ngày lễ": Chọn ngày bắt đầu - ngày kết thúc
- Với "Phí qua đêm": Không cần điều kiện thời gian

**Mức giá:**
- Nhập giá bằng VND (ví dụ: 5000, 10000)

**Mô tả:**
- Ghi chú thêm (tùy chọn)

### 2. Xóa cấu hình
- Click nút **thùng rác** (🗑️) ở góc phải card
- Xác nhận xóa

### 3. Lưu cấu hình
- Click nút "**Lưu tất cả cấu hình**" ở cuối trang
- Hệ thống sẽ lưu tất cả cấu hình của cả xe máy và xe hơi

### 4. Đặt lại
- Click nút "**Đặt lại**" để xóa tất cả cấu hình và bắt đầu lại

## Ví dụ cấu hình

### Ví dụ 1: Giá theo khung giờ
```
Loại: Khung giờ bình thường
Tên: Giá xe máy ban ngày
Giờ: 06:00 - 18:00
Giá: 5,000 VND
Mô tả: Áp dụng từ 6h sáng đến 6h chiều
```

### Ví dụ 2: Phí qua đêm
```
Loại: Phí qua đêm
Tên: Phí xe máy qua đêm
Giá: 10,000 VND
Mô tả: Phí cố định cho xe qua đêm
```

### Ví dụ 3: Ngày lễ Tết
```
Loại: Ngày lễ / Sự kiện
Tên: Phí Tết Nguyên Đán
Ngày: 01/02/2025 - 07/02/2025
Giá: 20,000 VND
Mô tả: Giá đặc biệt dịp Tết
```

### Ví dụ 4: Cuối tuần
```
Loại: Phụ phí cuối tuần
Tên: Phụ phí thứ 7 - CN
Giờ: 00:00 - 23:59
Giá: 8,000 VND
Mô tả: Phí tăng thêm vào cuối tuần
```

## Cấu trúc dữ liệu JSON

Khi lưu, hệ thống sẽ gửi dữ liệu dạng JSON:

```json
{
  "motorbike": [
    {
      "type": "normal",
      "name": "Giá xe máy ban ngày",
      "price": 5000,
      "start_time": "06:00",
      "end_time": "18:00",
      "description": "Áp dụng từ 6h sáng đến 6h chiều"
    },
    {
      "type": "overnight",
      "name": "Phí qua đêm",
      "price": 10000,
      "description": "Phí cố định"
    }
  ],
  "car": [
    {
      "type": "holiday",
      "name": "Phí Tết",
      "price": 30000,
      "start_date": "2025-02-01",
      "end_date": "2025-02-07",
      "description": "Giá đặc biệt dịp Tết"
    }
  ]
}
```

## Cập nhật backend để lưu vào database

Trong file `app.py`, route `/admin/pricing/save-dynamic` cần được cập nhật:

```python
@app.route('/admin/pricing/save-dynamic', methods=['POST'])
@login_required
def admin_pricing_save_dynamic():
    try:
        data = request.get_json()
        motorbike_configs = data.get('motorbike', [])
        car_configs = data.get('car', [])
        
        # Xóa cấu hình cũ
        execute_db("DELETE FROM pricing_rules WHERE vehicle_type=?", ['Xe máy'])
        execute_db("DELETE FROM pricing_rules WHERE vehicle_type=?", ['Xe hơi'])
        
        # Lưu cấu hình xe máy
        for config in motorbike_configs:
            execute_db(
                """INSERT INTO pricing_rules 
                   (vehicle_type, rule_type, name, price, start_time, end_time, 
                    start_date, end_date, description)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                [
                    'Xe máy',
                    config['type'],
                    config['name'],
                    config['price'],
                    config.get('start_time'),
                    config.get('end_time'),
                    config.get('start_date'),
                    config.get('end_date'),
                    config.get('description', '')
                ]
            )
        
        # Lưu cấu hình xe hơi
        for config in car_configs:
            execute_db(
                """INSERT INTO pricing_rules 
                   (vehicle_type, rule_type, name, price, start_time, end_time, 
                    start_date, end_date, description)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                [
                    'Xe hơi',
                    config['type'],
                    config['name'],
                    config['price'],
                    config.get('start_time'),
                    config.get('end_time'),
                    config.get('start_date'),
                    config.get('end_date'),
                    config.get('description', '')
                ]
            )
        
        return jsonify({
            'success': True,
            'message': f'Đã lưu {len(motorbike_configs)} cấu hình xe máy và {len(car_configs)} cấu hình xe hơi'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'})
```

## Tính năng nâng cao

### 1. Load cấu hình từ database
Thêm code để load cấu hình có sẵn khi mở trang:

```javascript
// Trong file pricing_dynamic.html
async function loadExistingConfigs() {
    try {
        const response = await fetch('/admin/pricing/get-dynamic');
        const data = await response.json();
        
        if (data.success) {
            // Render motorbike configs
            data.motorbike.forEach(config => {
                addConfigFromData('motorbike', config);
            });
            
            // Render car configs
            data.car.forEach(config => {
                addConfigFromData('car', config);
            });
        }
    } catch (error) {
        console.error('Error loading configs:', error);
    }
}

// Call on page load
document.addEventListener('DOMContentLoaded', loadExistingConfigs);
```

### 2. Validation
Thêm validation trước khi lưu:

```javascript
function validateConfigs() {
    const errors = [];
    
    // Check if at least one config exists
    const motorbikeCards = document.querySelectorAll('#motorbike-configs .config-card');
    const carCards = document.querySelectorAll('#car-configs .config-card');
    
    if (motorbikeCards.length === 0 && carCards.length === 0) {
        errors.push('Vui lòng thêm ít nhất một cấu hình');
    }
    
    // Check required fields
    document.querySelectorAll('.config-card').forEach(card => {
        const name = card.querySelector('.config-name').value;
        const price = card.querySelector('.config-price').value;
        
        if (!name) {
            errors.push('Vui lòng nhập tên cấu hình');
        }
        
        if (!price || price <= 0) {
            errors.push('Vui lòng nhập giá hợp lệ');
        }
    });
    
    return errors;
}
```

## Lưu ý
- Cấu hình sẽ được áp dụng theo độ ưu tiên (priority)
- Ngày lễ có độ ưu tiên cao nhất
- Phí qua đêm có độ ưu tiên thứ hai
- Khung giờ bình thường có độ ưu tiên thấp nhất

## Hỗ trợ
Nếu gặp vấn đề, vui lòng kiểm tra:
1. Database đã tạo bảng `pricing_rules` chưa
2. Route `/admin/pricing/save-dynamic` đã được thêm vào `app.py` chưa
3. Console log (F12) để xem lỗi JavaScript
4. Network tab để xem request/response

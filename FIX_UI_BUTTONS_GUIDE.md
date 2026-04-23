# 🔧 HƯỚNG DẪN FIX LỖI NÚT UI

## 🎯 MỤC TIÊU

Fix các lỗi thường gặp với nút "Xem", "Sửa", "Xóa" trong giao diện admin.

---

## 🐛 LỖI THƯỜNG GẶP

### Lỗi 1: Nút "Xem" không truyền ID
**Triệu chứng**: Click nút "Xem chi tiết" → Trang trắng hoặc 404

**Nguyên nhân**: Thiếu `id` trong URL hoặc form

**Giải pháp**:

#### Template (HTML):
```html
<!-- ❌ SAI -->
<a href="{{ url_for('card_detail') }}" class="btn btn-info">Xem</a>

<!-- ✅ ĐÚNG -->
<a href="{{ url_for('card_detail', card_id=card.id) }}" class="btn btn-info">Xem</a>
```

#### Route (Python):
```python
@app.route('/admin/card/<int:card_id>')
def card_detail(card_id):
    card = query_db("SELECT * FROM cards WHERE id = %s", [card_id], one=True)
    
    if not card:
        flash('Không tìm thấy thẻ!', 'error')
        return redirect(url_for('admin_cards'))
    
    return render_template('admin/card/detail.html', card=card)
```

---

### Lỗi 2: Form "Sửa" không load dữ liệu
**Triệu chứng**: Mở form sửa → Các field trống

**Nguyên nhân**: Không truyền dữ liệu từ backend sang template

**Giải pháp**:

#### Route (Python):
```python
@app.route('/admin/card/edit/<int:card_id>', methods=['GET', 'POST'])
def card_edit(card_id):
    if request.method == 'POST':
        # Xử lý update
        owner_name = request.form.get('owner_name')
        phone = request.form.get('phone')
        email = request.form.get('email')
        
        execute_db(
            "UPDATE cards SET owner_name = %s, phone = %s, email = %s WHERE id = %s",
            [owner_name, phone, email, card_id]
        )
        
        flash('Cập nhật thành công!', 'success')
        return redirect(url_for('admin_cards'))
    
    # GET - Load dữ liệu
    card = query_db("SELECT * FROM cards WHERE id = %s", [card_id], one=True)
    
    if not card:
        flash('Không tìm thấy thẻ!', 'error')
        return redirect(url_for('admin_cards'))
    
    return render_template('admin/card/edit.html', card=card)
```

#### Template (HTML):
```html
<form method="POST">
    <div class="form-group">
        <label>Tên chủ thẻ</label>
        <input type="text" name="owner_name" class="form-control" 
               value="{{ card.owner_name }}" required>
    </div>
    
    <div class="form-group">
        <label>Số điện thoại</label>
        <input type="text" name="phone" class="form-control" 
               value="{{ card.phone }}">
    </div>
    
    <div class="form-group">
        <label>Email</label>
        <input type="email" name="email" class="form-control" 
               value="{{ card.email }}">
    </div>
    
    <button type="submit" class="btn btn-primary">Lưu</button>
    <a href="{{ url_for('admin_cards') }}" class="btn btn-secondary">Hủy</a>
</form>
```

---

### Lỗi 3: Nút "Xóa" không có xác nhận
**Triệu chứng**: Click xóa → Xóa luôn không hỏi

**Nguyên nhân**: Thiếu JavaScript confirm

**Giải pháp**:

#### Template (HTML):
```html
<!-- ❌ SAI -->
<a href="{{ url_for('card_delete', card_id=card.id) }}" class="btn btn-danger">Xóa</a>

<!-- ✅ ĐÚNG - Cách 1: JavaScript inline -->
<a href="{{ url_for('card_delete', card_id=card.id) }}" 
   class="btn btn-danger"
   onclick="return confirm('Bạn có chắc muốn xóa thẻ này?')">
   Xóa
</a>

<!-- ✅ ĐÚNG - Cách 2: Form với POST -->
<form method="POST" action="{{ url_for('card_delete', card_id=card.id) }}" 
      style="display: inline;"
      onsubmit="return confirm('Bạn có chắc muốn xóa thẻ này?')">
    <button type="submit" class="btn btn-danger">Xóa</button>
</form>
```

#### Route (Python):
```python
@app.route('/admin/card/delete/<int:card_id>', methods=['POST'])
def card_delete(card_id):
    try:
        # Kiểm tra thẻ có tồn tại không
        card = query_db("SELECT * FROM cards WHERE id = %s", [card_id], one=True)
        
        if not card:
            flash('Không tìm thấy thẻ!', 'error')
            return redirect(url_for('admin_cards'))
        
        # Kiểm tra thẻ có đang được sử dụng không
        vehicles = query_db(
            "SELECT COUNT(*) as count FROM vehicles WHERE card_id = %s AND status = 'parked'",
            [card_id],
            one=True
        )
        
        if vehicles['count'] > 0:
            flash('Không thể xóa thẻ đang được sử dụng!', 'error')
            return redirect(url_for('admin_cards'))
        
        # Xóa thẻ
        execute_db("DELETE FROM cards WHERE id = %s", [card_id])
        
        flash('Xóa thẻ thành công!', 'success')
        return redirect(url_for('admin_cards'))
        
    except Exception as e:
        app.logger.error(f"❌ Error deleting card: {e}")
        flash('Lỗi hệ thống! Không thể xóa thẻ.', 'error')
        return redirect(url_for('admin_cards'))
```

---

### Lỗi 4: Form submit bị lỗi 500
**Triệu chứng**: Submit form → Trang trắng 500 Internal Server Error

**Nguyên nhân**: 
- Thiếu xử lý exception
- Tên field không khớp giữa HTML và Python
- Dữ liệu không hợp lệ

**Giải pháp**:

#### 1. Thêm try-except trong route:
```python
@app.route('/card/register', methods=['GET', 'POST'])
def card_register():
    if request.method == 'POST':
        try:
            # Lấy dữ liệu
            card_number = request.form.get('card_number', '').strip()
            owner_name = request.form.get('owner_name', '').strip()
            
            # Validate
            if not card_number or not owner_name:
                flash('Vui lòng nhập đầy đủ thông tin!', 'error')
                return redirect(url_for('card_register'))
            
            # Insert
            execute_db(
                "INSERT INTO cards (card_number, owner_name) VALUES (%s, %s)",
                [card_number, owner_name]
            )
            
            flash('Tạo thẻ thành công!', 'success')
            return redirect(url_for('admin_cards'))
            
        except Exception as e:
            app.logger.error(f"❌ Error: {e}")
            flash('Lỗi hệ thống! Vui lòng thử lại.', 'error')
            return redirect(url_for('card_register'))
    
    return render_template('card/register.html')
```

#### 2. Kiểm tra tên field khớp:
```html
<!-- HTML -->
<input type="text" name="card_number" required>
<input type="text" name="owner_name" required>
```

```python
# Python - Phải khớp với name trong HTML
card_number = request.form.get('card_number')  # ✅ Đúng
owner_name = request.form.get('owner_name')    # ✅ Đúng
```

---

## 📋 CHECKLIST RÀ SOÁT

### Cho mỗi trang admin (cards, vehicles, transactions, etc.):

- [ ] **Nút "Xem"**:
  - [ ] URL có truyền ID: `url_for('detail', id=item.id)`
  - [ ] Route có nhận ID: `@app.route('/detail/<int:id>')`
  - [ ] Có xử lý trường hợp không tìm thấy

- [ ] **Nút "Sửa"**:
  - [ ] URL có truyền ID
  - [ ] Form load đúng dữ liệu: `value="{{ item.field }}"`
  - [ ] Submit form có xử lý UPDATE
  - [ ] Có validate dữ liệu

- [ ] **Nút "Xóa"**:
  - [ ] Có confirm trước khi xóa
  - [ ] Dùng POST method (không dùng GET)
  - [ ] Kiểm tra ràng buộc trước khi xóa
  - [ ] Có xử lý lỗi

- [ ] **Form submit**:
  - [ ] Tên field khớp giữa HTML và Python
  - [ ] Có validate input
  - [ ] Có try-except xử lý lỗi
  - [ ] Có flash message thông báo
  - [ ] Redirect sau khi thành công

---

## 🔍 CÁCH KIỂM TRA

### 1. Kiểm tra logs:
```python
# Thêm logging vào route
app.logger.info(f"Received form data: {request.form}")
app.logger.info(f"Card ID: {card_id}")
```

### 2. Kiểm tra trong browser:
- Mở Developer Tools (F12)
- Tab Network → Xem request/response
- Tab Console → Xem JavaScript errors

### 3. Test từng chức năng:
```
1. Tạo mới → Kiểm tra INSERT
2. Xem chi tiết → Kiểm tra SELECT
3. Sửa → Kiểm tra UPDATE
4. Xóa → Kiểm tra DELETE
```

---

## ✅ TEMPLATE MẪU HOÀN CHỈNH

### admin/cards.html (Danh sách):
```html
<table class="table">
    <thead>
        <tr>
            <th>ID</th>
            <th>Số thẻ</th>
            <th>Chủ thẻ</th>
            <th>Số dư</th>
            <th>Thao tác</th>
        </tr>
    </thead>
    <tbody>
        {% for card in cards %}
        <tr>
            <td>{{ card.id }}</td>
            <td>{{ card.card_number }}</td>
            <td>{{ card.owner_name }}</td>
            <td>{{ "{:,}".format(card.balance) }} đ</td>
            <td>
                <a href="{{ url_for('card_detail', card_id=card.id) }}" 
                   class="btn btn-sm btn-info">Xem</a>
                
                <a href="{{ url_for('card_edit', card_id=card.id) }}" 
                   class="btn btn-sm btn-warning">Sửa</a>
                
                <form method="POST" 
                      action="{{ url_for('card_delete', card_id=card.id) }}" 
                      style="display: inline;"
                      onsubmit="return confirm('Bạn có chắc muốn xóa?')">
                    <button type="submit" class="btn btn-sm btn-danger">Xóa</button>
                </form>
            </td>
        </tr>
        {% endfor %}
    </tbody>
</table>
```

---

**Hoàn thành! Tất cả nút UI sẽ hoạt động đúng! ✅**

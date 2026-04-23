# 🎨 HƯỚNG DẪN ÁP DỤNG THEME POLISH

## 📋 Tổng quan

Hệ thống **Theme Polish** cung cấp giao diện Light/Dark mode chuyên nghiệp với:
- ✅ CSS Variables hoàn chỉnh cho cả 2 chế độ
- ✅ Màu sắc tinh tế, không chói mắt
- ✅ Biểu đồ tự động chuyển màu
- ✅ Transitions mượt mà
- ✅ Scrollbar tùy chỉnh
- ✅ Accessibility compliant

---

## 📁 Files đã tạo

```
static/
├── css/
│   └── theme-polish.css      ← CSS Variables & Styling chính
└── js/
    └── chart-theme.js         ← Quản lý màu biểu đồ tự động
```

---

## 🚀 BƯỚC 1: Thêm CSS vào HTML

### Cho file `admin/base.html`:

Thêm dòng này vào `<head>`, **TRƯỚC** các file CSS khác:

```html
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Admin - Quản lý bãi đỗ xe{% endblock %}</title>
    
    <!-- Google Fonts -->
    <link href="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    
    <!-- Bootstrap -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    
    <!-- Font Awesome -->
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    
    <!-- ✨ THEME POLISH - Thêm dòng này ✨ -->
    <link rel="stylesheet" href="/static/css/theme-polish.css">
    
    <!-- Global CSS (giữ nguyên) -->
    <link rel="stylesheet" href="/static/css/global.css">
    
    <!-- Smooth UX CSS (giữ nguyên) -->
    <link rel="stylesheet" href="/static/css/smooth-ux.css">
    
    <!-- Các style khác... -->
</head>
```

### Cho file `base.html` (trang người dùng):

```html
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Parking System{% endblock %}</title>

    <!-- Bootstrap -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    
    <!-- Font Awesome -->
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    
    <!-- ✨ THEME POLISH - Thêm dòng này ✨ -->
    <link rel="stylesheet" href="/static/css/theme-polish.css">
    
    <!-- Global CSS (giữ nguyên) -->
    <link rel="stylesheet" href="/static/css/global.css">
    
    {% block head %}{% endblock %}
</head>
```

---

## 🚀 BƯỚC 2: Thêm JavaScript cho Biểu đồ

### Nếu trang có biểu đồ (Chart.js):

Thêm vào **TRƯỚC** `</body>`:

```html
    <!-- Chart.js (nếu chưa có) -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    
    <!-- ✨ CHART THEME MANAGER - Thêm dòng này ✨ -->
    <script src="/static/js/chart-theme.js"></script>
    
    <!-- Smooth UX JS (giữ nguyên) -->
    <script src="/static/js/smooth-ux.js"></script>
    
    {% block scripts %}{% endblock %}
</body>
```

---

## 🎯 BƯỚC 3: Cập nhật Code Biểu đồ

### ❌ TRƯỚC (Code cũ):

```javascript
const ctx = document.getElementById('myChart').getContext('2d');
const myChart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: ['Jan', 'Feb', 'Mar'],
        datasets: [{
            label: 'Doanh thu',
            data: [12, 19, 3],
            borderColor: '#667eea',
            backgroundColor: 'rgba(102, 126, 234, 0.1)'
        }]
    },
    options: {
        responsive: true
    }
});
```

### ✅ SAU (Code mới - Tự động chuyển màu):

```javascript
// Cách 1: Dùng helper function (KHUYẾN NGHỊ)
const myChart = createThemedChart('myChart', {
    type: 'line',
    data: {
        labels: ['Jan', 'Feb', 'Mar'],
        datasets: [{
            label: 'Doanh thu',
            data: [12, 19, 3],
            fill: true  // Tự động tạo gradient
        }]
    }
    // options sẽ tự động merge với theme defaults
});

// Cách 2: Tạo thủ công và đăng ký
const ctx = document.getElementById('myChart').getContext('2d');
const myChart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: ['Jan', 'Feb', 'Mar'],
        datasets: [{
            label: 'Doanh thu',
            data: [12, 19, 3],
            fill: true,
            backgroundColor: createChartGradient(ctx, 'primary')
        }]
    },
    options: chartThemeManager.getChartDefaults()
});

// Đăng ký để tự động cập nhật khi đổi theme
registerChart('myChart', myChart);
```

---

## 🎨 BƯỚC 4: Sử dụng CSS Variables trong Code

### Trong CSS tùy chỉnh:

```css
/* ✅ ĐÚNG - Dùng CSS Variables */
.my-custom-card {
    background: var(--bg-surface);
    color: var(--text-primary);
    border: 1px solid var(--border-light);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-sm);
    transition: var(--transition-base);
}

.my-custom-card:hover {
    background: var(--bg-elevated);
    box-shadow: var(--shadow-md);
}

/* ❌ SAI - Hard-code màu */
.my-custom-card {
    background: #ffffff;
    color: #1e293b;
    border: 1px solid #e2e8f0;
}
```

### Trong JavaScript:

```javascript
// Lấy màu từ CSS Variables
const primaryColor = getComputedStyle(document.documentElement)
    .getPropertyValue('--primary').trim();

// Hoặc dùng helper function cho biểu đồ
const colors = getChartColors();
console.log(colors.textColor);  // Màu text theo theme hiện tại
```

---

## 🔧 BƯỚC 5: Cập nhật Inline Styles (Nếu có)

### ❌ TRƯỚC:

```html
<div style="background: #ffffff; color: #1e293b;">
    Nội dung
</div>
```

### ✅ SAU:

```html
<div style="background: var(--bg-surface); color: var(--text-primary);">
    Nội dung
</div>
```

Hoặc tốt hơn, dùng class:

```html
<div class="nqt-card">
    Nội dung
</div>
```

---

## 📊 BƯỚC 6: Ví dụ Biểu đồ Hoàn chỉnh

### Dashboard với nhiều biểu đồ:

```html
<div class="row">
    <div class="col-md-6">
        <div class="nqt-card">
            <div class="nqt-card-header">
                <h5 class="nqt-card-title">
                    <i class="fas fa-chart-line"></i>
                    Doanh thu theo tháng
                </h5>
            </div>
            <div class="nqt-card-body">
                <canvas id="revenueChart" height="300"></canvas>
            </div>
        </div>
    </div>
    
    <div class="col-md-6">
        <div class="nqt-card">
            <div class="nqt-card-header">
                <h5 class="nqt-card-title">
                    <i class="fas fa-chart-pie"></i>
                    Phân bố loại xe
                </h5>
            </div>
            <div class="nqt-card-body">
                <canvas id="vehicleChart" height="300"></canvas>
            </div>
        </div>
    </div>
</div>

<script>
// Biểu đồ doanh thu (Line chart với gradient)
const revenueChart = createThemedChart('revenueChart', {
    type: 'line',
    data: {
        labels: ['T1', 'T2', 'T3', 'T4', 'T5', 'T6'],
        datasets: [{
            label: 'Doanh thu (triệu VNĐ)',
            data: [12, 19, 15, 25, 22, 30],
            fill: true,
            tension: 0.4
        }]
    }
});

// Biểu đồ phân bố xe (Pie chart)
const vehicleChart = createThemedChart('vehicleChart', {
    type: 'pie',
    data: {
        labels: ['Xe máy', 'Ô tô', 'Xe đạp'],
        datasets: [{
            data: [300, 150, 50]
        }]
    }
});
</script>
```

---

## 🎯 CSS Variables Reference

### Màu sắc chính:

```css
/* Primary Colors */
--primary:        /* #667eea (light) | #8b9aef (dark) */
--primary-dark:   /* #764ba2 (light) | #9b7bc2 (dark) */
--primary-grad:   /* Gradient primary */

/* Semantic Colors */
--success:        /* #11998e (light) | #34d399 (dark) */
--warning:        /* #f59f00 (light) | #fbbf24 (dark) */
--danger:         /* #ef4444 (light) | #f87171 (dark) */
--info:           /* #4facfe (light) | #60a5fa (dark) */

/* Typography */
--text-primary:   /* #1e293b (light) | #e2e8f0 (dark) */
--text-secondary: /* #64748b (light) | #94a3b8 (dark) */
--text-muted:     /* #94a3b8 (light) | #64748b (dark) */

/* Backgrounds */
--bg-body:        /* #f8fafc (light) | #0f172a (dark) */
--bg-surface:     /* #ffffff (light) | #1e293b (dark) */
--bg-elevated:    /* #ffffff (light) | #334155 (dark) */
--bg-hover:       /* #f1f5f9 (light) | #475569 (dark) */

/* Borders */
--border-light:   /* #e2e8f0 (light) | rgba(255,255,255,0.08) (dark) */
--border-medium:  /* #cbd5e1 (light) | rgba(255,255,255,0.12) (dark) */

/* Shadows */
--shadow-sm:      /* Soft shadow (light) | Elevation border (dark) */
--shadow-md:      /* Medium shadow (light) | Elevation border (dark) */
--shadow-lg:      /* Large shadow (light) | Elevation border (dark) */

/* Border Radius */
--radius-sm:  8px
--radius-md:  12px
--radius-lg:  16px
--radius-xl:  20px

/* Transitions */
--transition-base:   all 0.25s ease
--transition-colors: background-color 0.3s ease, color 0.3s ease, border-color 0.3s ease
```

---

## 🧪 BƯỚC 7: Test & Verify

### Checklist:

- [ ] Chuyển Light/Dark mode → Màu sắc thay đổi mượt mà
- [ ] Biểu đồ tự động cập nhật màu khi đổi theme
- [ ] Không có màu trắng tinh (#FFF) hoặc đen thui (#000) trong Dark mode
- [ ] Scrollbar tùy chỉnh hoạt động
- [ ] Form controls có focus state rõ ràng
- [ ] Table rows có hover effect
- [ ] Badges và alerts hiển thị đúng màu
- [ ] Không có lỗi console
- [ ] Transitions không bị giật lag

### Test trong Console:

```javascript
// Test theme manager
console.log(chartThemeManager.currentTheme);  // 'light' hoặc 'dark'

// Test màu sắc
console.log(getChartColors());

// Test số biểu đồ đã đăng ký
console.log(chartThemeManager.charts.size);
```

---

## 🐛 Troubleshooting

### Vấn đề: Biểu đồ không đổi màu

**Giải pháp:**
1. Kiểm tra `chart-theme.js` đã load chưa
2. Dùng `createThemedChart()` thay vì `new Chart()`
3. Hoặc đăng ký thủ công: `registerChart('chartId', chartInstance)`

### Vấn đề: Màu sắc không đổi khi toggle theme

**Giải pháp:**
1. Kiểm tra `theme-polish.css` đã load **TRƯỚC** các file CSS khác
2. Đảm bảo dùng `var(--variable-name)` thay vì hard-code màu
3. Kiểm tra `data-theme="dark"` attribute trên `<body>`

### Vấn đề: Scrollbar không tùy chỉnh

**Giải pháp:**
- Scrollbar tùy chỉnh chỉ hoạt động trên Chromium browsers (Chrome, Edge, Opera)
- Firefox có hỗ trợ giới hạn qua `scrollbar-width` và `scrollbar-color`

### Vấn đề: Transitions bị giật

**Giải pháp:**
1. Kiểm tra không có `!important` conflict
2. Đảm bảo `transition` được định nghĩa trước khi thay đổi thuộc tính
3. Dùng `will-change` cho các element thường xuyên animate

---

## 📝 Notes

### ✅ Được phép làm:
- Thêm CSS Variables mới vào `:root` và `[data-theme="dark"]`
- Tùy chỉnh màu sắc trong `CHART_THEMES`
- Thêm class mới sử dụng CSS Variables
- Tạo biểu đồ mới với `createThemedChart()`

### ❌ KHÔNG được làm:
- Hard-code màu sắc (#fff, #000, rgb(), rgba()) trong CSS
- Xóa hoặc sửa logic trong `chart-theme.js`
- Thay đổi cấu trúc `data-theme` attribute
- Xóa `transition` properties

---

## 🎉 Kết quả mong đợi

Sau khi áp dụng, hệ thống sẽ có:

✅ **Light Mode:**
- Nền off-white (#f8fafc) thay vì trắng tinh
- Card nền trắng với shadow mềm
- Text màu xám đen (#1e293b)
- Biểu đồ với màu sắc rực rỡ

✅ **Dark Mode:**
- Nền xám đen sang trọng (#0f172a, #1e293b)
- Text xám nhạt (#e2e8f0) thay vì trắng
- Border sáng mỏng thay vì shadow
- Biểu đồ với màu sắc dịu hơn

✅ **Transitions:**
- Chuyển theme mượt mà trong 0.3s
- Không bị flash/chớp giật
- Biểu đồ animate khi cập nhật

---

## 📞 Support

Nếu gặp vấn đề, kiểm tra:
1. Console có lỗi không
2. Network tab → CSS/JS files đã load đúng chưa
3. Elements tab → `data-theme` attribute có đúng không
4. Computed styles → CSS Variables có giá trị đúng không

---

**Chúc bạn thành công! 🚀**

/**
 * ============================================
 * SMOOTH UX ENHANCEMENTS - GIAI ĐOẠN 3
 * Tối ưu trải nghiệm người dùng
 * ============================================
 */

// ── CONFIGURATION ──
const UX_CONFIG = {
    animationDuration: 300,
    toastDuration: 3000,
    loadingDelay: 500,
    debounceDelay: 300
};

// ── TOAST NOTIFICATIONS ──
class ToastManager {
    constructor() {
        this.container = this.createContainer();
    }

    createContainer() {
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.style.cssText = `
                position: fixed;
                top: 80px;
                right: 20px;
                z-index: 10000;
                display: flex;
                flex-direction: column;
                gap: 10px;
                max-width: 400px;
            `;
            document.body.appendChild(container);
        }
        return container;
    }

    show(message, type = 'info', duration = UX_CONFIG.toastDuration) {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        
        const icons = {
            success: '<i class="fas fa-check-circle"></i>',
            error: '<i class="fas fa-exclamation-circle"></i>',
            warning: '<i class="fas fa-exclamation-triangle"></i>',
            info: '<i class="fas fa-info-circle"></i>'
        };

        toast.innerHTML = `
            ${icons[type] || icons.info}
            <span>${message}</span>
            <button class="toast-close" onclick="this.parentElement.remove()">
                <i class="fas fa-times"></i>
            </button>
        `;

        this.container.appendChild(toast);

        // Animate in
        setTimeout(() => toast.classList.add('show'), 10);

        // Auto remove
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, duration);

        return toast;
    }

    success(message, duration) {
        return this.show(message, 'success', duration);
    }

    error(message, duration) {
        return this.show(message, 'error', duration);
    }

    warning(message, duration) {
        return this.show(message, 'warning', duration);
    }

    info(message, duration) {
        return this.show(message, 'info', duration);
    }
}

// Global toast instance
window.toast = new ToastManager();

// ── LOADING OVERLAY ──
class LoadingManager {
    constructor() {
        this.overlay = this.createOverlay();
        this.activeRequests = 0;
    }

    createOverlay() {
        let overlay = document.getElementById('loading-overlay');
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.id = 'loading-overlay';
            overlay.innerHTML = `
                <div class="loading-spinner">
                    <div class="spinner-ring"></div>
                    <div class="spinner-ring"></div>
                    <div class="spinner-ring"></div>
                    <div class="loading-text">Đang xử lý...</div>
                </div>
            `;
            document.body.appendChild(overlay);
        }
        return overlay;
    }

    show(text = 'Đang xử lý...') {
        this.activeRequests++;
        const textEl = this.overlay.querySelector('.loading-text');
        if (textEl) textEl.textContent = text;
        this.overlay.classList.add('active');
    }

    hide() {
        this.activeRequests = Math.max(0, this.activeRequests - 1);
        if (this.activeRequests === 0) {
            this.overlay.classList.remove('active');
        }
    }
}

// Global loading instance
window.loading = new LoadingManager();

// ── FETCH WITH LOADING ──
window.fetchWithLoading = async function(url, options = {}, loadingText = 'Đang xử lý...') {
    loading.show(loadingText);
    try {
        const response = await fetch(url, options);
        const data = await response.json();
        loading.hide();
        return { success: true, data, response };
    } catch (error) {
        loading.hide();
        toast.error('Lỗi kết nối: ' + error.message);
        return { success: false, error };
    }
};

// ── CONFIRM DIALOG ──
window.confirmAction = function(message, onConfirm, onCancel) {
    const overlay = document.createElement('div');
    overlay.className = 'confirm-overlay';
    overlay.innerHTML = `
        <div class="confirm-dialog">
            <div class="confirm-icon">
                <i class="fas fa-question-circle"></i>
            </div>
            <div class="confirm-message">${message}</div>
            <div class="confirm-buttons">
                <button class="btn-confirm-cancel">
                    <i class="fas fa-times"></i> Hủy
                </button>
                <button class="btn-confirm-ok">
                    <i class="fas fa-check"></i> Xác nhận
                </button>
            </div>
        </div>
    `;

    document.body.appendChild(overlay);
    setTimeout(() => overlay.classList.add('show'), 10);

    const btnCancel = overlay.querySelector('.btn-confirm-cancel');
    const btnOk = overlay.querySelector('.btn-confirm-ok');

    const close = () => {
        overlay.classList.remove('show');
        setTimeout(() => overlay.remove(), 300);
    };

    btnCancel.onclick = () => {
        close();
        if (onCancel) onCancel();
    };

    btnOk.onclick = () => {
        close();
        if (onConfirm) onConfirm();
    };

    overlay.onclick = (e) => {
        if (e.target === overlay) {
            close();
            if (onCancel) onCancel();
        }
    };
};

// ── DEBOUNCE UTILITY ──
window.debounce = function(func, delay = UX_CONFIG.debounceDelay) {
    let timeoutId;
    return function(...args) {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => func.apply(this, args), delay);
    };
};

// ── SMOOTH SCROLL ──
window.smoothScrollTo = function(element, offset = 0) {
    const targetPosition = element.getBoundingClientRect().top + window.pageYOffset - offset;
    window.scrollTo({
        top: targetPosition,
        behavior: 'smooth'
    });
};

// ── FORM VALIDATION ──
window.validateForm = function(formElement) {
    const inputs = formElement.querySelectorAll('input[required], select[required], textarea[required]');
    let isValid = true;
    let firstInvalid = null;

    inputs.forEach(input => {
        if (!input.value.trim()) {
            isValid = false;
            input.classList.add('is-invalid');
            if (!firstInvalid) firstInvalid = input;
        } else {
            input.classList.remove('is-invalid');
        }
    });

    if (!isValid && firstInvalid) {
        firstInvalid.focus();
        toast.warning('Vui lòng điền đầy đủ thông tin bắt buộc');
    }

    return isValid;
};

// ── AUTO-SAVE INDICATOR ──
class AutoSaveIndicator {
    constructor() {
        this.indicator = this.createIndicator();
    }

    createIndicator() {
        let indicator = document.getElementById('autosave-indicator');
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.id = 'autosave-indicator';
            indicator.innerHTML = '<i class="fas fa-check"></i> Đã lưu';
            document.body.appendChild(indicator);
        }
        return indicator;
    }

    show(message = 'Đã lưu', type = 'success') {
        const icons = {
            success: 'fa-check',
            saving: 'fa-spinner fa-spin',
            error: 'fa-exclamation-circle'
        };
        this.indicator.innerHTML = `<i class="fas ${icons[type]}"></i> ${message}`;
        this.indicator.className = `autosave-${type}`;
        this.indicator.classList.add('show');

        if (type === 'success' || type === 'error') {
            setTimeout(() => {
                this.indicator.classList.remove('show');
            }, 2000);
        }
    }

    saving() {
        this.show('Đang lưu...', 'saving');
    }

    saved() {
        this.show('Đã lưu', 'success');
    }

    error() {
        this.show('Lỗi lưu', 'error');
    }
}

window.autoSave = new AutoSaveIndicator();

// ── CHART ANIMATIONS ──
window.animateChart = function(chart) {
    chart.options.animation = {
        duration: 1000,
        easing: 'easeInOutQuart',
        onComplete: function() {
            console.log('Chart animation complete');
        }
    };
    chart.update();
};

// ── TABLE ENHANCEMENTS ──
window.enhanceTable = function(tableElement) {
    // Add row hover effects
    const rows = tableElement.querySelectorAll('tbody tr');
    rows.forEach(row => {
        row.style.transition = 'all 0.3s ease';
    });

    // Add sort functionality
    const headers = tableElement.querySelectorAll('thead th[data-sortable]');
    headers.forEach(header => {
        header.style.cursor = 'pointer';
        header.innerHTML += ' <i class="fas fa-sort sort-icon"></i>';
        
        header.addEventListener('click', function() {
            const column = this.cellIndex;
            const rows = Array.from(tableElement.querySelectorAll('tbody tr'));
            const isAscending = this.classList.contains('sort-asc');
            
            // Remove all sort classes
            headers.forEach(h => h.classList.remove('sort-asc', 'sort-desc'));
            
            // Add new sort class
            this.classList.add(isAscending ? 'sort-desc' : 'sort-asc');
            
            // Sort rows
            rows.sort((a, b) => {
                const aValue = a.cells[column].textContent.trim();
                const bValue = b.cells[column].textContent.trim();
                return isAscending ? 
                    bValue.localeCompare(aValue, 'vi') : 
                    aValue.localeCompare(bValue, 'vi');
            });
            
            // Reappend rows
            const tbody = tableElement.querySelector('tbody');
            rows.forEach(row => tbody.appendChild(row));
        });
    });
};

// ── INITIALIZE ON DOM READY ──
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Smooth UX initialized');
    
    // Add smooth scroll to all anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) smoothScrollTo(target, 80);
        });
    });

    // Auto-validate forms on submit
    document.querySelectorAll('form[data-validate]').forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!validateForm(this)) {
                e.preventDefault();
            }
        });
    });

    // Enhance all tables with data-enhance attribute
    document.querySelectorAll('table[data-enhance]').forEach(table => {
        enhanceTable(table);
    });
});

console.log('✅ smooth-ux.js loaded successfully');

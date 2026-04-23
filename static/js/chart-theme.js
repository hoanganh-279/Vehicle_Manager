/* ============================================
   CHART THEME MANAGER
   Tự động cập nhật màu sắc biểu đồ theo Dark/Light Mode
   ============================================ */

/**
 * Hàm tạo biểu đồ với theme tự động
 * @param {string} canvasId - ID của canvas element
 * @param {object} config - Cấu hình Chart.js
 * @returns {Chart} - Instance của Chart.js
 */
function createThemedChart(canvasId, config) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) {
        console.error(`Canvas with id "${canvasId}" not found`);
        return null;
    }

    // Lấy theme hiện tại
    const isDark = document.body.getAttribute('data-theme') === 'dark';
    
    // Apply theme colors to config
    applyThemeToChartConfig(config, isDark);
    
    // Tạo chart
    const chart = new Chart(canvas, config);
    
    // Lưu chart instance để có thể update sau
    if (!window.themedCharts) {
        window.themedCharts = {};
    }
    window.themedCharts[canvasId] = chart;
    
    return chart;
}

/**
 * Apply theme colors vào config của Chart.js
 */
function applyThemeToChartConfig(config, isDark) {
    // Define color palettes
    const colors = {
        light: {
            gridColor: 'rgba(0, 0, 0, 0.05)',
            textColor: '#64748b',
            tooltipBg: 'rgba(255, 255, 255, 0.95)',
            tooltipText: '#1e293b',
            tooltipBorder: '#e2e8f0',
            legendText: '#475569'
        },
        dark: {
            gridColor: 'rgba(255, 255, 255, 0.05)',
            textColor: '#A0A0A0',
            tooltipBg: 'rgba(42, 42, 42, 0.95)',
            tooltipText: '#F8F9FA',
            tooltipBorder: 'rgba(255, 255, 255, 0.1)',
            legendText: '#B3B3B3'
        }
    };
    
    const theme = isDark ? colors.dark : colors.light;
    
    // Ensure options object exists
    if (!config.options) {
        config.options = {};
    }
    
    // ── SCALES CONFIGURATION ──
    if (!config.options.scales) {
        config.options.scales = {};
    }
    
    // X Axis
    if (config.options.scales.x !== false) {
        config.options.scales.x = {
            ...config.options.scales.x,
            ticks: {
                ...config.options.scales.x?.ticks,
                color: theme.textColor,
                font: {
                    size: 11,
                    ...config.options.scales.x?.ticks?.font
                }
            },
            grid: {
                ...config.options.scales.x?.grid,
                color: theme.gridColor,
                drawBorder: false
            },
            border: {
                display: false
            }
        };
    }
    
    // Y Axis
    if (config.options.scales.y !== false) {
        config.options.scales.y = {
            ...config.options.scales.y,
            ticks: {
                ...config.options.scales.y?.ticks,
                color: theme.textColor,
                font: {
                    size: 11,
                    ...config.options.scales.y?.ticks?.font
                }
            },
            grid: {
                ...config.options.scales.y?.grid,
                color: theme.gridColor,
                drawBorder: false
            },
            border: {
                display: false
            }
        };
    }
    
    // ── PLUGINS CONFIGURATION ──
    if (!config.options.plugins) {
        config.options.plugins = {};
    }
    
    // Legend
    if (config.options.plugins.legend !== false) {
        config.options.plugins.legend = {
            ...config.options.plugins.legend,
            labels: {
                ...config.options.plugins.legend?.labels,
                color: theme.legendText,
                font: {
                    size: 12,
                    weight: '600',
                    ...config.options.plugins.legend?.labels?.font
                }
            }
        };
    }
    
    // Title
    if (config.options.plugins.title && config.options.plugins.title.display) {
        config.options.plugins.title = {
            ...config.options.plugins.title,
            color: theme.textColor,
            font: {
                size: 14,
                weight: '700',
                ...config.options.plugins.title?.font
            }
        };
    }
    
    // Tooltip
    config.options.plugins.tooltip = {
        ...config.options.plugins.tooltip,
        backgroundColor: theme.tooltipBg,
        titleColor: theme.tooltipText,
        bodyColor: theme.tooltipText,
        borderColor: theme.tooltipBorder,
        borderWidth: 1,
        padding: 12,
        cornerRadius: 8,
        displayColors: true,
        boxPadding: 6,
        titleFont: {
            size: 13,
            weight: '700'
        },
        bodyFont: {
            size: 12,
            weight: '500'
        },
        callbacks: {
            ...config.options.plugins.tooltip?.callbacks
        }
    };
}

/**
 * Update tất cả biểu đồ khi theme thay đổi
 */
function updateAllChartsTheme() {
    if (!window.themedCharts) return;
    
    const isDark = document.body.getAttribute('data-theme') === 'dark';
    
    Object.keys(window.themedCharts).forEach(canvasId => {
        const chart = window.themedCharts[canvasId];
        if (chart && chart.config) {
            applyThemeToChartConfig(chart.config, isDark);
            chart.update('none'); // Update without animation
        }
    });
}

/**
 * Destroy một biểu đồ cụ thể
 */
function destroyThemedChart(canvasId) {
    if (window.themedCharts && window.themedCharts[canvasId]) {
        window.themedCharts[canvasId].destroy();
        delete window.themedCharts[canvasId];
    }
}

/**
 * Destroy tất cả biểu đồ
 */
function destroyAllThemedCharts() {
    if (!window.themedCharts) return;
    
    Object.keys(window.themedCharts).forEach(canvasId => {
        destroyThemedChart(canvasId);
    });
}

// ── AUTO-UPDATE CHARTS WHEN THEME CHANGES ──
// Lắng nghe sự kiện thay đổi theme
const originalToggleTheme = window.toggleTheme;
if (originalToggleTheme) {
    window.toggleTheme = function() {
        originalToggleTheme();
        // Đợi một chút để theme được apply
        setTimeout(() => {
            updateAllChartsTheme();
        }, 50);
    };
}

// Observe theme changes (fallback method)
const themeObserver = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
        if (mutation.type === 'attributes' && mutation.attributeName === 'data-theme') {
            updateAllChartsTheme();
        }
    });
});

// Start observing
if (document.body) {
    themeObserver.observe(document.body, {
        attributes: true,
        attributeFilter: ['data-theme']
    });
}

// ── HELPER FUNCTIONS ──

/**
 * Get current theme
 */
function getCurrentTheme() {
    return document.body.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
}

/**
 * Check if dark mode is active
 */
function isDarkMode() {
    return getCurrentTheme() === 'dark';
}

/**
 * Get theme colors
 */
function getThemeColors() {
    const isDark = isDarkMode();
    return {
        gridColor: isDark ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)',
        textColor: isDark ? '#A0A0A0' : '#64748b',
        tooltipBg: isDark ? 'rgba(42, 42, 42, 0.95)' : 'rgba(255, 255, 255, 0.95)',
        tooltipText: isDark ? '#F8F9FA' : '#1e293b',
        tooltipBorder: isDark ? 'rgba(255, 255, 255, 0.1)' : '#e2e8f0',
        legendText: isDark ? '#B3B3B3' : '#475569'
    };
}

// Export functions to global scope
window.createThemedChart = createThemedChart;
window.updateAllChartsTheme = updateAllChartsTheme;
window.destroyThemedChart = destroyThemedChart;
window.destroyAllThemedCharts = destroyAllThemedCharts;
window.getCurrentTheme = getCurrentTheme;
window.isDarkMode = isDarkMode;
window.getThemeColors = getThemeColors;

console.log('✅ Chart Theme Manager loaded successfully');

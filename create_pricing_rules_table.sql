-- Tạo bảng pricing_rules cho Dynamic Rule-based Pricing
-- Bảng này lưu trữ các quy tắc giá động

CREATE TABLE pricing_rules (
    id INT IDENTITY(1,1) PRIMARY KEY,
    vehicle_type NVARCHAR(50) NOT NULL,  -- 'Xe máy' hoặc 'Xe hơi'
    rule_type NVARCHAR(50) NOT NULL,     -- 'normal', 'overnight', 'holiday', 'weekend'
    name NVARCHAR(200) NOT NULL,         -- Tên cấu hình
    price INT NOT NULL,                  -- Mức giá (VND)
    start_time TIME NULL,                -- Giờ bắt đầu (cho normal/weekend)
    end_time TIME NULL,                  -- Giờ kết thúc (cho normal/weekend)
    start_date DATE NULL,                -- Ngày bắt đầu (cho holiday)
    end_date DATE NULL,                  -- Ngày kết thúc (cho holiday)
    description NVARCHAR(500) NULL,      -- Mô tả thêm
    priority INT DEFAULT 0,              -- Độ ưu tiên (số càng cao càng ưu tiên)
    is_active BIT DEFAULT 1,             -- Trạng thái kích hoạt
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME DEFAULT GETDATE()
);

-- Tạo index để tăng tốc truy vấn
CREATE INDEX idx_pricing_rules_vehicle_type ON pricing_rules(vehicle_type);
CREATE INDEX idx_pricing_rules_rule_type ON pricing_rules(rule_type);
CREATE INDEX idx_pricing_rules_active ON pricing_rules(is_active);

-- Thêm dữ liệu mẫu
INSERT INTO pricing_rules (vehicle_type, rule_type, name, price, start_time, end_time, description, priority)
VALUES 
    (N'Xe máy', 'normal', N'Giá ban ngày', 5000, '06:00', '18:00', N'Giá áp dụng từ 6h sáng đến 6h chiều', 1),
    (N'Xe máy', 'normal', N'Giá ban đêm', 3000, '18:00', '06:00', N'Giá áp dụng từ 6h chiều đến 6h sáng', 1),
    (N'Xe máy', 'overnight', N'Phí qua đêm', 10000, NULL, NULL, N'Phí cố định cho xe qua đêm', 2),
    (N'Xe hơi', 'normal', N'Giá ban ngày', 15000, '06:00', '18:00', N'Giá áp dụng từ 6h sáng đến 6h chiều', 1),
    (N'Xe hơi', 'normal', N'Giá ban đêm', 10000, '18:00', '06:00', N'Giá áp dụng từ 6h chiều đến 6h sáng', 1),
    (N'Xe hơi', 'overnight', N'Phí qua đêm', 30000, NULL, NULL, N'Phí cố định cho xe qua đêm', 2);

-- Hiển thị dữ liệu vừa thêm
SELECT * FROM pricing_rules ORDER BY vehicle_type, priority DESC, id;

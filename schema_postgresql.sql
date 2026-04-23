-- ═══════════════════════════════════════════════════════════════════════════
-- POSTGRESQL SCHEMA FOR PARKING MANAGEMENT SYSTEM
-- Converted from T-SQL to PostgreSQL
-- ═══════════════════════════════════════════════════════════════════════════

-- Drop tables if exist (for clean install)
DROP TABLE IF EXISTS balance_history CASCADE;
DROP TABLE IF EXISTS topup_transactions CASCADE;
DROP TABLE IF EXISTS vehicles CASCADE;
DROP TABLE IF EXISTS cards CASCADE;
DROP TABLE IF EXISTS parking_config CASCADE;
DROP TABLE IF EXISTS pricing_rules CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- ═══════════════════════════════════════════════════════════════════════════
-- TABLE: users (Admin users)
-- ═══════════════════════════════════════════════════════════════════════════
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(200),
    email VARCHAR(200),
    role VARCHAR(50) DEFAULT 'admin',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ═══════════════════════════════════════════════════════════════════════════
-- TABLE: parking_config (System configuration)
-- ═══════════════════════════════════════════════════════════════════════════
CREATE TABLE parking_config (
    id SERIAL PRIMARY KEY,
    motorbike_capacity INTEGER DEFAULT 100,
    car_capacity INTEGER DEFAULT 50,
    motorbike_rate INTEGER DEFAULT 5000,
    car_rate INTEGER DEFAULT 15000,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default config
INSERT INTO parking_config (motorbike_capacity, car_capacity, motorbike_rate, car_rate)
VALUES (100, 50, 5000, 15000);

-- ═══════════════════════════════════════════════════════════════════════════
-- TABLE: pricing_rules (Dynamic pricing)
-- ═══════════════════════════════════════════════════════════════════════════
CREATE TABLE pricing_rules (
    id SERIAL PRIMARY KEY,
    vehicle_type VARCHAR(50) NOT NULL,
    time_from TIME NOT NULL,
    time_to TIME NOT NULL,
    rate INTEGER NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ═══════════════════════════════════════════════════════════════════════════
-- TABLE: cards (Member cards)
-- ═══════════════════════════════════════════════════════════════════════════
CREATE TABLE cards (
    id SERIAL PRIMARY KEY,
    card_number VARCHAR(50) UNIQUE NOT NULL,
    owner_name VARCHAR(200),
    phone VARCHAR(20),
    email VARCHAR(200),
    balance DECIMAL(18, 2) DEFAULT 0,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for fast lookup
CREATE INDEX idx_cards_card_number ON cards(card_number);
CREATE INDEX idx_cards_phone ON cards(phone);

-- ═══════════════════════════════════════════════════════════════════════════
-- TABLE: vehicles (Parking records)
-- ═══════════════════════════════════════════════════════════════════════════
CREATE TABLE vehicles (
    id SERIAL PRIMARY KEY,
    license_plate VARCHAR(20) NOT NULL,
    plate_color VARCHAR(50),
    vehicle_type VARCHAR(50) NOT NULL,
    plate_type VARCHAR(50),
    status VARCHAR(50) DEFAULT 'parked',
    entry_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    exit_time TIMESTAMP,
    actual_fee DECIMAL(18, 2),
    payment_status VARCHAR(50) DEFAULT 'unpaid',
    payment_method VARCHAR(50),
    card_id INTEGER REFERENCES cards(id),
    spot_id INTEGER,
    parking_spot_id INTEGER,
    momo_trans_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_vehicles_license_plate ON vehicles(license_plate);
CREATE INDEX idx_vehicles_status ON vehicles(status);
CREATE INDEX idx_vehicles_entry_time ON vehicles(entry_time);
CREATE INDEX idx_vehicles_card_id ON vehicles(card_id);
CREATE INDEX idx_vehicles_momo_trans_id ON vehicles(momo_trans_id);

-- ═══════════════════════════════════════════════════════════════════════════
-- TABLE: topup_transactions (Card topup history)
-- ═══════════════════════════════════════════════════════════════════════════
CREATE TABLE topup_transactions (
    id SERIAL PRIMARY KEY,
    card_id INTEGER NOT NULL REFERENCES cards(id),
    amount DECIMAL(18, 2) NOT NULL,
    payment_method VARCHAR(50) DEFAULT 'momo',
    status VARCHAR(50) DEFAULT 'pending',
    transaction_id VARCHAR(100) UNIQUE NOT NULL,
    momo_trans_id VARCHAR(100) UNIQUE,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_topup_card_id ON topup_transactions(card_id);
CREATE INDEX idx_topup_transaction_id ON topup_transactions(transaction_id);
CREATE UNIQUE INDEX idx_topup_momo_trans_id ON topup_transactions(momo_trans_id) WHERE momo_trans_id IS NOT NULL;

-- ═══════════════════════════════════════════════════════════════════════════
-- TABLE: balance_history (Audit trail for card balance changes)
-- ═══════════════════════════════════════════════════════════════════════════
CREATE TABLE balance_history (
    id SERIAL PRIMARY KEY,
    card_id INTEGER NOT NULL REFERENCES cards(id),
    amount DECIMAL(18, 2) NOT NULL,
    balance_before DECIMAL(18, 2) NOT NULL,
    balance_after DECIMAL(18, 2) NOT NULL,
    type VARCHAR(50) NOT NULL,
    description TEXT,
    transaction_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    ip_address VARCHAR(50)
);

-- Indexes
CREATE INDEX idx_balance_history_card_id ON balance_history(card_id);
CREATE INDEX idx_balance_history_created_at ON balance_history(created_at);
CREATE INDEX idx_balance_history_transaction_id ON balance_history(transaction_id);

-- ═══════════════════════════════════════════════════════════════════════════
-- TRIGGER: Auto-update updated_at timestamp
-- ═══════════════════════════════════════════════════════════════════════════
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to tables
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_cards_updated_at BEFORE UPDATE ON cards
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_vehicles_updated_at BEFORE UPDATE ON vehicles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_parking_config_updated_at BEFORE UPDATE ON parking_config
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ═══════════════════════════════════════════════════════════════════════════
-- SAMPLE DATA (Optional - for testing)
-- ═══════════════════════════════════════════════════════════════════════════

-- Admin user (password: admin123 - hashed with bcrypt)
INSERT INTO users (username, password_hash, full_name, email, role)
VALUES ('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYIq.Hn8jiq', 'Administrator', 'admin@parking.com', 'admin');

-- Sample cards
INSERT INTO cards (card_number, owner_name, phone, email, balance, status)
VALUES 
    ('CARD001', 'Nguyen Van A', '0901234567', 'nguyenvana@email.com', 100000, 'active'),
    ('CARD002', 'Tran Thi B', '0912345678', 'tranthib@email.com', 50000, 'active');

-- ═══════════════════════════════════════════════════════════════════════════
-- VIEWS (Optional - for reporting)
-- ═══════════════════════════════════════════════════════════════════════════

-- View: Current parking status
CREATE OR REPLACE VIEW v_current_parking AS
SELECT 
    v.id,
    v.license_plate,
    v.vehicle_type,
    v.entry_time,
    EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - v.entry_time))/3600 AS hours_parked,
    c.card_number,
    c.owner_name,
    v.spot_id
FROM vehicles v
LEFT JOIN cards c ON v.card_id = c.id
WHERE v.status = 'parked'
ORDER BY v.entry_time DESC;

-- View: Daily revenue
CREATE OR REPLACE VIEW v_daily_revenue AS
SELECT 
    DATE(exit_time) AS date,
    vehicle_type,
    COUNT(*) AS total_vehicles,
    SUM(actual_fee) AS total_revenue
FROM vehicles
WHERE status = 'exited' AND payment_status = 'paid'
GROUP BY DATE(exit_time), vehicle_type
ORDER BY date DESC;

-- ═══════════════════════════════════════════════════════════════════════════
-- COMPLETED
-- ═══════════════════════════════════════════════════════════════════════════

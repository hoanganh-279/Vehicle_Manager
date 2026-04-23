USE ParkingManagement;
GO

-- Fix vehicle_type
UPDATE vehicles SET vehicle_type = N'Xe máy' WHERE vehicle_type = 'motorbike' OR vehicle_type = N'motorbike';
UPDATE vehicles SET vehicle_type = N'Xe hơi' WHERE vehicle_type = 'car' OR vehicle_type = N'car';

-- Fix plate_color bị lỗi encoding (Tráº¯ng = Trắng bị lỗi)
UPDATE vehicles SET plate_color = N'Trắng' WHERE plate_color NOT IN (N'Trắng', N'Vàng', N'Xanh', N'Đỏ');

-- Fix plate_type
UPDATE vehicles SET plate_type = N'Biển thường' WHERE plate_type = N'Thường' OR plate_type = 'Thường';
UPDATE vehicles SET plate_type = N'Biển thường' WHERE plate_type IS NULL OR plate_type = '';

-- Kiểm tra kết quả
SELECT DISTINCT vehicle_type FROM vehicles;
SELECT DISTINCT plate_color FROM vehicles;
SELECT DISTINCT plate_type FROM vehicles;
GO

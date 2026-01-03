-- ============================================================================
-- LabTrack Database Setup Script for Supabase
-- ============================================================================
-- This script creates all necessary tables, relationships, and indexes
-- for the LabTrack Inventory Management System.
--
-- Instructions:
-- 1. Open your Supabase project dashboard
-- 2. Go to SQL Editor
-- 3. Paste this entire script
-- 4. Click "Run" to execute
-- ============================================================================

-- ============================================================================
-- 1. INVENTORY TABLE
-- ============================================================================
-- Stores component types (e.g., "Arduino", "Raspberry Pi")
-- Each inventory record represents a type of component, not individual items
CREATE TABLE IF NOT EXISTS inventory (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    total_qty INTEGER NOT NULL DEFAULT 0,
    course TEXT,
    description TEXT,
    custom_fields JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add unique constraint on name to prevent duplicates
ALTER TABLE inventory ADD CONSTRAINT inventory_name_unique UNIQUE (name);

-- Add index for faster lookups by name
CREATE INDEX IF NOT EXISTS idx_inventory_name ON inventory(name);
CREATE INDEX IF NOT EXISTS idx_inventory_course ON inventory(course);

-- ============================================================================
-- 2. ITEMS TABLE
-- ============================================================================
-- Stores individual physical items with unique serial numbers
-- Each item belongs to an inventory type
CREATE TABLE IF NOT EXISTS items (
    id BIGSERIAL PRIMARY KEY,
    serial_number TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL DEFAULT 'Available' CHECK (status IN ('Available', 'Issued', 'Damaged')),
    inventory_id BIGINT NOT NULL REFERENCES inventory(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_items_serial_number ON items(serial_number);
CREATE INDEX IF NOT EXISTS idx_items_inventory_id ON items(inventory_id);
CREATE INDEX IF NOT EXISTS idx_items_status ON items(status);
CREATE INDEX IF NOT EXISTS idx_items_inventory_status ON items(inventory_id, status);

-- ============================================================================
-- 3. STUDENTS TABLE
-- ============================================================================
-- Stores student information for tracking who has items issued
CREATE TABLE IF NOT EXISTS students (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    student_id TEXT NOT NULL UNIQUE,
    phone TEXT,
    email TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_students_student_id ON students(student_id);
CREATE INDEX IF NOT EXISTS idx_students_name ON students(name);

-- ============================================================================
-- 4. STAFF TABLE
-- ============================================================================
-- Stores staff/issuer information for tracking who issued items
CREATE TABLE IF NOT EXISTS staff (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    staff_id TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add index for faster lookups
CREATE INDEX IF NOT EXISTS idx_staff_staff_id ON staff(staff_id);
CREATE INDEX IF NOT EXISTS idx_staff_name ON staff(name);

-- ============================================================================
-- 5. TRANSACTIONS TABLE
-- ============================================================================
-- Stores transaction records (when items are issued to students)
CREATE TABLE IF NOT EXISTS transactions (
    id BIGSERIAL PRIMARY KEY,
    student_id BIGINT NOT NULL REFERENCES students(id) ON DELETE RESTRICT,
    issuer_id BIGINT REFERENCES staff(id) ON DELETE SET NULL,
    status TEXT NOT NULL DEFAULT 'Active' CHECK (status IN ('Active', 'Completed')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    issue_date DATE NOT NULL DEFAULT CURRENT_DATE,
    expected_return_date DATE,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_transactions_student_id ON transactions(student_id);
CREATE INDEX IF NOT EXISTS idx_transactions_issuer_id ON transactions(issuer_id);
CREATE INDEX IF NOT EXISTS idx_transactions_status ON transactions(status);
CREATE INDEX IF NOT EXISTS idx_transactions_issue_date ON transactions(issue_date);
CREATE INDEX IF NOT EXISTS idx_transactions_expected_return_date ON transactions(expected_return_date);

-- ============================================================================
-- 6. TRANSACTION_ITEMS TABLE (Junction Table)
-- ============================================================================
-- Links transactions to items (many-to-many relationship)
-- One transaction can have multiple items, one item can be in multiple transactions over time
CREATE TABLE IF NOT EXISTS transaction_items (
    id BIGSERIAL PRIMARY KEY,
    transaction_id BIGINT NOT NULL REFERENCES transactions(id) ON DELETE CASCADE,
    item_id BIGINT NOT NULL REFERENCES items(id) ON DELETE RESTRICT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(transaction_id, item_id)  -- Prevent duplicate entries
);

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_transaction_items_transaction_id ON transaction_items(transaction_id);
CREATE INDEX IF NOT EXISTS idx_transaction_items_item_id ON transaction_items(item_id);

-- ============================================================================
-- 7. TRIGGERS FOR UPDATED_AT TIMESTAMPS
-- ============================================================================
-- Automatically update updated_at timestamp when records are modified

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to all tables with updated_at
CREATE TRIGGER update_inventory_updated_at BEFORE UPDATE ON inventory
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_items_updated_at BEFORE UPDATE ON items
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_students_updated_at BEFORE UPDATE ON students
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_staff_updated_at BEFORE UPDATE ON staff
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_transactions_updated_at BEFORE UPDATE ON transactions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- 8. ROW LEVEL SECURITY (RLS) POLICIES
-- ============================================================================
-- Enable RLS on all tables (Supabase best practice)
-- Adjust these policies based on your security requirements

ALTER TABLE inventory ENABLE ROW LEVEL SECURITY;
ALTER TABLE items ENABLE ROW LEVEL SECURITY;
ALTER TABLE students ENABLE ROW LEVEL SECURITY;
ALTER TABLE staff ENABLE ROW LEVEL SECURITY;
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE transaction_items ENABLE ROW LEVEL SECURITY;

-- Policy: Allow all operations for authenticated users
-- NOTE: Adjust these policies based on your authentication setup
-- For development, you might want to allow all operations:
CREATE POLICY "Allow all for authenticated users" ON inventory
    FOR ALL USING (true);

CREATE POLICY "Allow all for authenticated users" ON items
    FOR ALL USING (true);

CREATE POLICY "Allow all for authenticated users" ON students
    FOR ALL USING (true);

CREATE POLICY "Allow all for authenticated users" ON staff
    FOR ALL USING (true);

CREATE POLICY "Allow all for authenticated users" ON transactions
    FOR ALL USING (true);

CREATE POLICY "Allow all for authenticated users" ON transaction_items
    FOR ALL USING (true);

-- ============================================================================
-- 9. SAMPLE DATA (OPTIONAL - FOR TESTING)
-- ============================================================================
-- Uncomment the section below to insert sample data for testing

/*
-- Insert sample inventory
INSERT INTO inventory (name, total_qty, course, description) VALUES
    ('Arduino Uno', 10, 'ECE101', 'Microcontroller board for embedded systems'),
    ('Raspberry Pi 4', 5, 'CS201', 'Single-board computer for IoT projects'),
    ('Ultrasonic Sensor', 20, 'ECE101', 'HC-SR04 distance measurement sensor'),
    ('LED Strip', 15, 'ECE102', 'WS2812B addressable RGB LED strip')
ON CONFLICT (name) DO NOTHING;

-- Insert sample students
INSERT INTO students (name, student_id, phone, email) VALUES
    ('John Doe', 'STU001', '555-0101', 'john.doe@university.edu'),
    ('Jane Smith', 'STU002', '555-0102', 'jane.smith@university.edu'),
    ('Bob Johnson', 'STU003', '555-0103', 'bob.johnson@university.edu'),
    ('Alice Williams', 'STU004', '555-0104', 'alice.williams@university.edu')
ON CONFLICT (student_id) DO NOTHING;

-- Insert sample staff
INSERT INTO staff (name, staff_id) VALUES
    ('Dr. Sarah Chen', 'STAFF001'),
    ('Prof. Michael Brown', 'STAFF002'),
    ('Lab Assistant', 'STAFF003')
ON CONFLICT (staff_id) DO NOTHING;

-- Insert sample items (get inventory IDs first)
DO $$
DECLARE
    arduino_id BIGINT;
    rpi_id BIGINT;
    sensor_id BIGINT;
    led_id BIGINT;
BEGIN
    SELECT id INTO arduino_id FROM inventory WHERE name = 'Arduino Uno';
    SELECT id INTO rpi_id FROM inventory WHERE name = 'Raspberry Pi 4';
    SELECT id INTO sensor_id FROM inventory WHERE name = 'Ultrasonic Sensor';
    SELECT id INTO led_id FROM inventory WHERE name = 'LED Strip';
    
    -- Arduino items
    INSERT INTO items (serial_number, status, inventory_id) VALUES
        ('ARD001', 'Available', arduino_id),
        ('ARD002', 'Available', arduino_id),
        ('ARD003', 'Issued', arduino_id),
        ('ARD004', 'Damaged', arduino_id),
        ('ARD005', 'Available', arduino_id)
    ON CONFLICT (serial_number) DO NOTHING;
    
    -- Raspberry Pi items
    INSERT INTO items (serial_number, status, inventory_id) VALUES
        ('RPI001', 'Available', rpi_id),
        ('RPI002', 'Available', rpi_id),
        ('RPI003', 'Issued', rpi_id)
    ON CONFLICT (serial_number) DO NOTHING;
    
    -- Sensor items
    INSERT INTO items (serial_number, status, inventory_id) VALUES
        ('SEN001', 'Available', sensor_id),
        ('SEN002', 'Available', sensor_id),
        ('SEN003', 'Issued', sensor_id)
    ON CONFLICT (serial_number) DO NOTHING;
    
    -- LED items
    INSERT INTO items (serial_number, status, inventory_id) VALUES
        ('LED001', 'Available', led_id),
        ('LED002', 'Available', led_id)
    ON CONFLICT (serial_number) DO NOTHING;
END $$;
*/

-- ============================================================================
-- 10. VERIFICATION QUERIES
-- ============================================================================
-- Run these queries to verify your setup:

-- Check all tables exist
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
    AND table_name IN ('inventory', 'items', 'students', 'staff', 'transactions', 'transaction_items')
ORDER BY table_name;

-- Check foreign key constraints
SELECT
    tc.table_name, 
    kcu.column_name, 
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name 
FROM information_schema.table_constraints AS tc 
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
    AND tc.table_schema = 'public'
ORDER BY tc.table_name;

-- Check indexes
SELECT 
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
    AND tablename IN ('inventory', 'items', 'students', 'staff', 'transactions', 'transaction_items')
ORDER BY tablename, indexname;

-- ============================================================================
-- SETUP COMPLETE!
-- ============================================================================
-- Your database is now ready to use with LabTrack.
-- 
-- Next steps:
-- 1. Update your .env file with SUPABASE_URL and SUPABASE_KEY
-- 2. Test the connection by running the LabTrack application
-- 3. Use the application to add inventory, students, and staff
-- 4. Start issuing items to students!
-- ============================================================================


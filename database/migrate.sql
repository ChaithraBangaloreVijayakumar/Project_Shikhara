-- =============================================================================
-- Project Shikhara — Migration Script
-- Normalises JSONB contact and opening hours columns into separate tables
-- =============================================================================


-- -----------------------------------------------------------------------------
-- Step 1: Create ENUM types
-- -----------------------------------------------------------------------------
CREATE TYPE contact_type AS ENUM (
    'phone', 'email', 'facebook', 'instagram', 'website'
);

CREATE TYPE day_of_week AS ENUM (
    'Monday', 'Tuesday', 'Wednesday', 'Thursday',
    'Friday', 'Saturday', 'Sunday', 'Closed'
);


-- -----------------------------------------------------------------------------
-- Step 2: Create new tables
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS temple_contact (
    id              SERIAL          PRIMARY KEY,
    temple_id       INT             NOT NULL REFERENCES temples(id) ON DELETE CASCADE,
    contact_type    contact_type    NOT NULL,
    value           TEXT            NOT NULL
);

CREATE TABLE IF NOT EXISTS temple_hours (
    id              SERIAL          PRIMARY KEY,
    temple_id       INT             NOT NULL REFERENCES temples(id) ON DELETE CASCADE,
    day             day_of_week     NOT NULL,
    hours           VARCHAR(50)     NOT NULL
);


-- -----------------------------------------------------------------------------
-- Step 3: Migrate contact data from temples into temple_contact
-- Each JSONB array is unnested into individual rows
-- -----------------------------------------------------------------------------

-- Phone
INSERT INTO temple_contact (temple_id, contact_type, value)
SELECT id, 'phone', jsonb_array_elements_text(contact_phone)
FROM temples
WHERE contact_phone IS NOT NULL;

-- Email
INSERT INTO temple_contact (temple_id, contact_type, value)
SELECT id, 'email', jsonb_array_elements_text(contact_email)
FROM temples
WHERE contact_email IS NOT NULL;

-- Facebook
INSERT INTO temple_contact (temple_id, contact_type, value)
SELECT id, 'facebook', jsonb_array_elements_text(contact_facebook)
FROM temples
WHERE contact_facebook IS NOT NULL;

-- Instagram
INSERT INTO temple_contact (temple_id, contact_type, value)
SELECT id, 'instagram', jsonb_array_elements_text(contact_instagram)
FROM temples
WHERE contact_instagram IS NOT NULL;

-- Website
INSERT INTO temple_contact (temple_id, contact_type, value)
SELECT id, 'website', jsonb_array_elements_text(website::jsonb)
FROM temples
WHERE website IS NOT NULL;


-- -----------------------------------------------------------------------------
-- Step 4: Migrate opening hours from temples into temple_hours
-- The JSONB object is expanded into key-value pairs (day → hours string)
-- -----------------------------------------------------------------------------
INSERT INTO temple_hours (temple_id, day, hours)
SELECT
    id,
    (kv).key::day_of_week,
    (kv).value::text
FROM temples,
     jsonb_each(opening_hours) AS kv
WHERE opening_hours IS NOT NULL
  AND (kv).value::text != 'null';


-- -----------------------------------------------------------------------------
-- Step 5: Drop migrated columns from temples
-- Only after confirming data has been moved successfully
-- -----------------------------------------------------------------------------
ALTER TABLE temples
    DROP COLUMN contact_phone,
    DROP COLUMN contact_email,
    DROP COLUMN contact_facebook,
    DROP COLUMN contact_instagram,
    DROP COLUMN website,
    DROP COLUMN opening_hours;


-- -----------------------------------------------------------------------------
-- Step 6: Add indexes on foreign keys for fast joins
-- -----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_temple_contact_temple_id ON temple_contact(temple_id);
CREATE INDEX IF NOT EXISTS idx_temple_hours_temple_id ON temple_hours(temple_id);


-- -----------------------------------------------------------------------------
-- Step 7: Verify — quick row counts across all tables
-- -----------------------------------------------------------------------------
SELECT 'location' AS table_name, COUNT(*) AS rows FROM location
UNION ALL
SELECT 'temples', COUNT(*) FROM temples
UNION ALL
SELECT 'temple_contact', COUNT(*) FROM temple_contact
UNION ALL
SELECT 'temple_hours', COUNT(*) FROM temple_hours;
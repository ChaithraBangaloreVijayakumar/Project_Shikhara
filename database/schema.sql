-- =============================================================================
-- Project Shikhara — Database Schema
-- =============================================================================

-- Enable pgvector extension (needed for RAG/chatbot embeddings later)
-- CREATE EXTENSION IF NOT EXISTS vector;


-- -----------------------------------------------------------------------------
-- Table: location
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS location (
    postal_code     VARCHAR(5)      PRIMARY KEY,
    state           VARCHAR(50)     NOT NULL
);


-- -----------------------------------------------------------------------------
-- Table: temples
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS temples (
    id                  SERIAL          PRIMARY KEY,
    name                VARCHAR(255)    NOT NULL,
    street              VARCHAR(255),
    postal_code         VARCHAR(5)      REFERENCES location(postal_code),
    city                VARCHAR(100),
    location_latitude   DECIMAL(9, 6),
    location_longitude  DECIMAL(9, 6),
    note                TEXT,
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_temples_name_street_city UNIQUE (name, street, city)
);


-- -----------------------------------------------------------------------------
-- ENUMs and child tables
-- -----------------------------------------------------------------------------
DO $$ BEGIN
    CREATE TYPE contact_type AS ENUM ('phone', 'email', 'facebook', 'instagram', 'website');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE day_of_week AS ENUM ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday', 'Closed');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

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
-- Trigger
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER temples_set_updated_at
    BEFORE UPDATE ON temples
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();


-- -----------------------------------------------------------------------------
-- Indexes
-- -----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_temples_postal_code ON temples(postal_code);
CREATE INDEX IF NOT EXISTS idx_temples_city ON temples(city);
CREATE INDEX IF NOT EXISTS idx_temples_lat_lon ON temples(location_latitude, location_longitude);
CREATE INDEX IF NOT EXISTS idx_temple_contact_temple_id ON temple_contact(temple_id);
CREATE INDEX IF NOT EXISTS idx_temple_hours_temple_id ON temple_hours(temple_id);
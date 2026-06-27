-- =============================================================================
-- Project Shikhara — Database Schema
-- =============================================================================

-- Enable pgvector extension (needed for RAG/chatbot embeddings later)
CREATE EXTENSION IF NOT EXISTS vector;


-- -----------------------------------------------------------------------------
-- Table: location
-- Source: moralescastillo/datasets — postal-code-germany.csv
-- One row per German postal code, mapping it to its Bundesland
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS location (
    postal_code     VARCHAR(5)      PRIMARY KEY,
    state           VARCHAR(50)     NOT NULL
);


-- -----------------------------------------------------------------------------
-- Table: temples
-- Core table — one row per Hindu temple in Germany
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS temples (
    id                  SERIAL          PRIMARY KEY,
    name                VARCHAR(255)    NOT NULL,
    street              VARCHAR(255),
    postal_code         VARCHAR(5)      REFERENCES location(postal_code),
    city                VARCHAR(100),
    location_latitude   DECIMAL(9, 6),
    location_longitude  DECIMAL(9, 6),
    website             TEXT,
    contact_phone       JSONB,
    contact_email       JSONB,
    contact_facebook    JSONB,
    contact_instagram   JSONB,
    opening_hours       JSONB,
    note                TEXT,
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);


-- -----------------------------------------------------------------------------
-- Auto-update updated_at on every row update
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER temples_set_updated_at
    BEFORE UPDATE ON temples
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();


-- -----------------------------------------------------------------------------
-- Indexes
-- -----------------------------------------------------------------------------

-- Fast state-level grouping via the location join
CREATE INDEX IF NOT EXISTS idx_temples_postal_code ON temples(postal_code);

-- Useful for map queries filtering by city
CREATE INDEX IF NOT EXISTS idx_temples_city ON temples(city);

-- Spatial index for map radius queries
CREATE INDEX IF NOT EXISTS idx_temples_lat_lon ON temples(location_latitude, location_longitude);
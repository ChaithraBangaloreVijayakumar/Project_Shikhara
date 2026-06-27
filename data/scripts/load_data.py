"""
Data loading script for Project Shikhara.
Loads location, temples, temple_contact and temple_hours tables into PostgreSQL.
Usage: python load_data.py <transformed_csv>
"""

import argparse
import json
import os

import pandas as pd
import psycopg2
from dotenv import load_dotenv

load_dotenv()


# ── Database connection ───────────────────────────────────────────────────────

def get_connection():
    return psycopg2.connect(
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT'),
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )


# ── Helpers ───────────────────────────────────────────────────────────────────

def parse_json(val):
    """Safely parse a JSON string into a Python object. Returns None on failure."""
    if pd.isna(val):
        return None
    try:
        return json.loads(val)
    except (json.JSONDecodeError, TypeError):
        return None


def null(val):
    """Return None if value is NaN, otherwise return the value."""
    return None if pd.isna(val) else val


# ── Load location table ───────────────────────────────────────────────────────

def load_location(conn):
    print("Loading location table from GitHub...")

    df = pd.read_csv(
        'https://raw.githubusercontent.com/moralescastillo/datasets/main/postal-code-germany.csv',
        dtype={'code': str}
    )
    df = df[['code', 'federal_state']].rename(columns={
        'code': 'postal_code',
        'federal_state': 'state'
    })

    with conn.cursor() as cur:
        for _, row in df.iterrows():
            cur.execute("""
                INSERT INTO location (postal_code, state)
                VALUES (%s, %s)
                ON CONFLICT (postal_code) DO UPDATE
                    SET state = EXCLUDED.state
            """, (row['postal_code'], row['state']))

    conn.commit()
    print(f"  ✅ Loaded {len(df)} rows into location table")


# ── Load temples, temple_contact, temple_hours ────────────────────────────────

def load_temples(conn, csv_path):
    print(f"Loading temples from {csv_path}...")

    df = pd.read_csv(csv_path, encoding='utf-8-sig', dtype={'postal_code': str})

    inserted, updated = 0, 0

    with conn.cursor() as cur:
        for _, row in df.iterrows():

            # 1. Upsert into temples on name + street + city
            cur.execute("""
                INSERT INTO temples (name, street, postal_code, city,
                    location_latitude, location_longitude, note)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (name, street, city) DO UPDATE
                    SET postal_code        = EXCLUDED.postal_code,
                        location_latitude  = EXCLUDED.location_latitude,
                        location_longitude = EXCLUDED.location_longitude,
                        note               = EXCLUDED.note,
                        updated_at         = NOW()
                RETURNING id, (xmax = 0) AS is_insert
            """, (
                row.get('name'),
                null(row.get('street')),
                null(row.get('postal_code')),
                null(row.get('city')),
                null(row.get('location_latitude')),
                null(row.get('location_longitude')),
                null(row.get('note')),
            ))

            temple_id, is_insert = cur.fetchone()
            if is_insert:
                inserted += 1
            else:
                updated += 1

            # 2. Replace contact rows for this temple
            cur.execute("DELETE FROM temple_contact WHERE temple_id = %s", (temple_id,))

            contact_fields = {
                'phone':     parse_json(row.get('contact_phone')),
                'email':     parse_json(row.get('contact_email_id')),
                'facebook':  parse_json(row.get('contact_facebook')),
                'instagram': parse_json(row.get('contact_instagram')),
                'website':   parse_json(row.get('website')),
            }

            for contact_type, values in contact_fields.items():
                if values:
                    for value in values:
                        cur.execute("""
                            INSERT INTO temple_contact (temple_id, contact_type, value)
                            VALUES (%s, %s, %s)
                        """, (temple_id, contact_type, value))

            # 3. Replace hours rows for this temple
            cur.execute("DELETE FROM temple_hours WHERE temple_id = %s", (temple_id,))

            hours = parse_json(row.get('opening_hours'))
            if hours:
                for day, time_str in hours.items():
                    if time_str:
                        cur.execute("""
                            INSERT INTO temple_hours (temple_id, day, hours)
                            VALUES (%s, %s, %s)
                        """, (temple_id, day, time_str))

    conn.commit()
    print(f"  ✅ Inserted: {inserted} | Updated: {updated}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main(csv_path):
    conn = get_connection()
    try:
        load_location(conn)
        load_temples(conn, csv_path)
        print("\n✅ Database loaded successfully.")
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Error: {e}")
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Load temple data into PostgreSQL.')
    parser.add_argument('input', help='Path to transformed_data.csv')
    args = parser.parse_args()
    main(args.input)
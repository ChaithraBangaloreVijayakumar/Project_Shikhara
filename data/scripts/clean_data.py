"""
Data cleaning script for Project Shikhara temple data.
Usage: python clean_data.py <input_csv> <output_csv>
"""

import argparse
import json
import os
import re
import sys

import pandas as pd


# ── Germany bounding box ──────────────────────────────────────────────────────
GERMANY_LAT = (47.2, 55.1)
GERMANY_LON = (5.9, 15.1)


# ── Opening hours parser ──────────────────────────────────────────────────────

def to_24h(time_str, assumed_period=None):
    """Convert a time string like '6', '7:30', '10 AM' to 'HH:MM'. 
    Returns (time_24h, was_assumed) where was_assumed=True if AM/PM was inferred."""
    time_str = time_str.strip()
    was_assumed = False

    period_match = re.search(r'(AM|PM)', time_str, re.IGNORECASE)
    if period_match:
        period = period_match.group(1).upper()
        time_str = re.sub(r'\s*(AM|PM)', '', time_str, flags=re.IGNORECASE).strip()
    elif assumed_period:
        period = assumed_period
        was_assumed = True
    else:
        return None, False

    parts = time_str.split(':')
    if not parts[0].strip().isdigit():
        return None, False
    hour = int(parts[0])
    minute = int(parts[1]) if len(parts) > 1 else 0

    if period == 'AM':
        if hour == 12:
            hour = 0
    else:  # PM
        if hour != 12:
            hour += 12

    return f"{hour:02d}:{minute:02d}", was_assumed


def parse_time_range(range_str):
    """Parse 'X AM to Y PM' or 'X to Y PM' into ('HH:MM', 'HH:MM', was_assumed).
    Returns None on failure."""
    range_str = range_str.strip()
    parts = re.split(r'\s+to\s+', range_str, flags=re.IGNORECASE)
    if len(parts) != 2:
        return None

    start_str, end_str = parts

    # Parse end time first to get its period (needed for ambiguous start times)
    end_period_match = re.search(r'(AM|PM)', end_str, re.IGNORECASE)
    end_period = end_period_match.group(1).upper() if end_period_match else None

    end_time, _ = to_24h(end_str)
    if end_time is None:
        return None

    start_time, was_assumed = to_24h(start_str, assumed_period=end_period)
    if start_time is None:
        return None

    return start_time, end_time, was_assumed


def parse_hours_string(hours_str):
    """Parse a full hours string (may contain two ranges separated by comma).
    Returns (formatted_string, was_assumed)."""
    if pd.isna(hours_str):
        return None, False

    hours_str = hours_str.strip()

    if hours_str.lower() == 'closed':
        return 'Closed', False
    if hours_str.lower() == 'open 24 hours':
        return '00:00–24:00', False

    segments = [s.strip() for s in hours_str.split(',')]
    results = []
    any_assumed = False

    for segment in segments:
        parsed = parse_time_range(segment)
        if parsed is None:
            return None, False  # Corrupted entry — return null
        start, end, assumed = parsed
        prefix = '~' if assumed else ''
        results.append(f"{prefix}{start}–{end}")
        if assumed:
            any_assumed = True

    return ', '.join(results), any_assumed


def build_opening_hours_json(row):
    """Collapse the 14 opening hours columns into a single dict.
    Returns (json_string, list_of_flagged_days)."""
    result = {}
    flagged_days = []

    for i in range(7):
        day_col = f'Opening_Hours_{i}_day'
        hour_col = f'Opening_Hours_{i}_hours'

        day = row.get(day_col)
        hours = row.get(hour_col)

        if pd.isna(day) or pd.isna(hours):
            continue

        parsed, was_assumed = parse_hours_string(hours)
        result[day] = parsed if parsed is not None else None

        if was_assumed:
            flagged_days.append(f"{day} ({hours})")

    return json.dumps(result) if result else None, flagged_days


# ── URL helpers ───────────────────────────────────────────────────────────────

def normalise_url(url):
    if pd.isna(url):
        return None
    url = url.strip().rstrip('/')
    if url and not url.startswith('http'):
        url = 'https://' + url
    return url


def normalise_url_list(value):
    """Handle comma-separated URLs — stored as JSON list."""
    if pd.isna(value):
        return None
    urls = [normalise_url(u) for u in value.split(',') if normalise_url(u)]
    return json.dumps(urls)


# ── Phone helpers ─────────────────────────────────────────────────────────────

def normalise_phone(phone_str):
    """Standardise phone numbers to +49 XXX XXXXXXX format, stored as JSON list."""
    if pd.isna(phone_str):
        return None

    numbers = [p.strip() for p in re.split(r'[\n,]', phone_str) if p.strip()]
    cleaned = []
    for num in numbers:
        num = re.sub(r'[\-\(\)]', ' ', num)   # replace dashes/parens with space
        num = re.sub(r'\s+', ' ', num).strip() # collapse multiple spaces
        if not num.startswith('+49'):
            num = '+49 ' + num.lstrip('0')
        cleaned.append(num)

    return json.dumps(cleaned)


# ── Email helpers ─────────────────────────────────────────────────────────────

def normalise_email(email_str):
    """Clean comma-separated emails into a JSON list."""
    if pd.isna(email_str):
        return None
    emails = [e.strip().lower() for e in email_str.split(',') if e.strip()]
    return json.dumps(emails)


# ── Upsert ───────────────────────────────────────────────────────────────────

UPSERT_KEY = ['name', 'street', 'city']

def upsert(existing, new):
    """Upsert new rows into existing dataframe on name + street + city.
    - Match found → overwrite that row with new data
    - No match → append as new row
    Columns in new but not in existing are ignored.
    Columns in existing but not in new are set to null for new rows."""

    # Only keep columns that already exist in the transformed file
    shared_cols = [c for c in new.columns if c in existing.columns]
    new = new[shared_cols]

    # Align new rows to existing column order, filling any missing cols with null
    new = new.reindex(columns=existing.columns)

    result = existing.copy()

    updated, appended = 0, 0
    for _, new_row in new.iterrows():
        match = (
            (result['name'] == new_row['name']) &
            (result['street'] == new_row['street']) &
            (result['city'] == new_row['city'])
        )
        if match.any():
            result.loc[match, :] = new_row.values
            updated += 1
        else:
            result = pd.concat([result, new_row.to_frame().T], ignore_index=True)
            appended += 1

    print(f"  Updated: {updated} rows | Appended: {appended} rows")
    return result


# ── Main ──────────────────────────────────────────────────────────────────────

def clean(input_path):
    """Read and clean the input CSV. Returns cleaned dataframe and oh_flags."""
    df = pd.read_csv(input_path, encoding='utf-8-sig')
    print(f"Loaded {len(df)} rows from {input_path}")

    # 1. Filter rows — drop only explicitly marked INVALID or UNSURE
    df = df[~df['Validity'].isin(['INVALID', 'UNSURE'])].copy()
    print(f"After filtering invalid/unsure: {len(df)} rows")

    # 2. Drop columns that exist — skip if already absent
    drop_cols = [c for c in ['Name_raw', 'Category_Name', 'Validity', 'permanentlyClosed'] if c in df.columns]
    df.drop(columns=drop_cols, inplace=True)



    # 4. Phone numbers
    if 'Contact_Phone' in df.columns:
        df['Contact_Phone'] = df['Contact_Phone'].apply(normalise_phone)

    # 5. Emails
    if 'Contact_Email_ID' in df.columns:
        df['Contact_Email_ID'] = df['Contact_Email_ID'].apply(normalise_email)

    # 6. URLs
    for col in ['Website', 'Contact_Facebook', 'Contact_Instagram']:
        if col in df.columns:
            df[col] = df[col].apply(normalise_url_list)

    # 7. Opening hours → single JSON column + flags
    oh_flags = {}
    oh_cols = [c for c in df.columns if c.startswith('Opening_Hours_')]
    if oh_cols:
        oh_json = []
        for _, row in df.iterrows():
            hours_json, flagged = build_opening_hours_json(row)
            oh_json.append(hours_json)
            if flagged:
                oh_flags[row['Name']] = flagged
        df['opening_hours'] = oh_json
        df.drop(columns=oh_cols, inplace=True)

    # 8. Postal code → string (preserve leading zeros)
    if 'Postal Code' in df.columns:
        df['Postal Code'] = df['Postal Code'].apply(
            lambda x: str(int(x)).zfill(5) if pd.notna(x) else None
        ).astype(str)

    # 9. Lat/lon bounds check
    if 'Location_latitude' in df.columns and 'Location_longitude' in df.columns:
        out_of_bounds = df[
            ~df['Location_latitude'].between(*GERMANY_LAT) |
            ~df['Location_longitude'].between(*GERMANY_LON)
        ][['Name', 'Location_latitude', 'Location_longitude']]
        if not out_of_bounds.empty:
            print("\n⚠️  Coordinates outside Germany:")
            print(out_of_bounds.to_string(index=False))

    # 10. Note column — strip whitespace
    if 'Note' in df.columns:
        df['Note'] = df['Note'].apply(lambda x: x.strip() if pd.notna(x) else None)

    # 11. Snake_case column names
    df.columns = [c.lower().replace(' ', '_') for c in df.columns]

    return df, oh_flags


def main(input_path, output_path):
    df_new, oh_flags = clean(input_path)

    # If output file already exists — upsert; otherwise save fresh
    if os.path.exists(output_path):
        print(f"\nExisting file found at {output_path} — upserting...")
        df_existing = pd.read_csv(output_path, encoding='utf-8-sig', dtype={'postal_code': str})
        df_final = upsert(df_existing, df_new)
    else:
        print("\nNo existing file found — saving fresh.")
        df_final = df_new

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df_final.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"\n✅ Saved {len(df_final)} rows to {output_path}")

    # Print AM/PM assumption flags
    if oh_flags:
        print("\n⚠️  Opening hours with assumed AM/PM (marked with ~ in JSON):")
        for temple, days in oh_flags.items():
            print(f"  {temple}:")
            for d in days:
                print(f"    → {d}")
    else:
        print("\n✅ No AM/PM assumptions needed.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Clean temple data CSV.')
    parser.add_argument('input', help='Path to input CSV')
    parser.add_argument('output', help='Path to output CSV')
    args = parser.parse_args()
    main(args.input, args.output)
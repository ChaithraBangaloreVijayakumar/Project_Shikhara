"""
Temple endpoints for Project Shikhara API.
"""

import math
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from psycopg2.extras import RealDictCursor

from database import get_db
from models import (
    PaginatedTemples, Temple,
    TempleContact, TempleHours
)

router = APIRouter(prefix="/temples", tags=["temples"])


# ── Helpers ───────────────────────────────────────────────────────────────────

def build_google_maps_url(name, street, city, postal_code):
    """Construct a Google Maps search URL using temple name and address."""
    if not any([street, city, postal_code]):
        return None
    address = ", ".join(filter(None, [street, city, postal_code, "Germany"]))
    query = f"{name}, {address}" if name else address
    return f"https://www.google.com/maps/search/?api=1&query={query.replace(' ', '+')}"


def build_temple(row, contacts, hours):
    """Assemble a Temple model from database rows."""
    contact = TempleContact(
        phone=    [c['value'] for c in contacts if c['contact_type'] == 'phone'],
        email=    [c['value'] for c in contacts if c['contact_type'] == 'email'],
        website=  [c['value'] for c in contacts if c['contact_type'] == 'website'],
        facebook= [c['value'] for c in contacts if c['contact_type'] == 'facebook'],
        instagram=[c['value'] for c in contacts if c['contact_type'] == 'instagram'],
    )

    opening_hours = TempleHours(**{h['day']: h['hours'] for h in hours})

    return Temple(
        id=                 row['id'],
        name=               row['name'],
        street=             row['street'],
        city=               row['city'],
        postal_code=        row['postal_code'],
        state=              row['state'],
        location_latitude=  row['location_latitude'],
        location_longitude= row['location_longitude'],
        google_maps_url=    build_google_maps_url(row['name'], row['street'], row['city'], row['postal_code']),
        note=               row['note'],
        contact=            contact,
        opening_hours=      opening_hours,
    )


def fetch_temples_data(cur, where_clause="", where_params=(), page=1, page_size=15):
    """Fetch paginated temples with their contacts and hours."""

    # Total count for pagination
    cur.execute(f"""
        SELECT COUNT(DISTINCT t.id)
        FROM temples t
        LEFT JOIN location l ON t.postal_code = l.postal_code
        {where_clause}
    """, where_params)
    total = cur.fetchone()['count']

    # Paginated temple ids
    offset = (page - 1) * page_size
    cur.execute(f"""
        SELECT t.id
        FROM temples t
        LEFT JOIN location l ON t.postal_code = l.postal_code
        {where_clause}
        ORDER BY t.name
        LIMIT %s OFFSET %s
    """, where_params + (page_size, offset))
    temple_ids = [r['id'] for r in cur.fetchall()]

    if not temple_ids:
        return [], total

    # Fetch core temple data
    cur.execute("""
        SELECT t.*, l.state
        FROM temples t
        LEFT JOIN location l ON t.postal_code = l.postal_code
        WHERE t.id = ANY(%s)
        ORDER BY t.name
    """, (temple_ids,))
    temples_rows = cur.fetchall()

    # Fetch all contacts for these temples
    cur.execute("""
        SELECT temple_id, contact_type, value
        FROM temple_contact
        WHERE temple_id = ANY(%s)
    """, (temple_ids,))
    contacts_rows = cur.fetchall()

    # Fetch all hours for these temples
    cur.execute("""
        SELECT temple_id, day, hours
        FROM temple_hours
        WHERE temple_id = ANY(%s)
    """, (temple_ids,))
    hours_rows = cur.fetchall()

    # Group contacts and hours by temple_id
    contacts_by_id = {tid: [] for tid in temple_ids}
    for c in contacts_rows:
        contacts_by_id[c['temple_id']].append(c)

    hours_by_id = {tid: [] for tid in temple_ids}
    for h in hours_rows:
        hours_by_id[h['temple_id']].append(h)

    # Assemble Temple models
    temples = [
        build_temple(row, contacts_by_id[row['id']], hours_by_id[row['id']])
        for row in temples_rows
    ]

    return temples, total


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("", response_model=PaginatedTemples)
def get_temples(
    city:       Optional[str] = Query(None),
    state:      Optional[str] = Query(None),
    page:       int = Query(1, ge=1),
    page_size:  int = Query(15, ge=1, le=100),
    conn=Depends(get_db)
):
    """Get all temples with optional city or state filter. Paginated."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:

        if city:
            where = "WHERE t.city = %s"
            params = (city,)
        elif state:
            where = "WHERE l.state = %s"
            params = (state,)
        else:
            where = ""
            params = ()

        temples, total = fetch_temples_data(cur, where, params, page, page_size)

    return PaginatedTemples(
        total=      total,
        page=       page,
        page_size=  page_size,
        pages=      math.ceil(total / page_size),
        data=       temples
    )


@router.get("/{temple_id}", response_model=Temple)
def get_temple(temple_id: int, conn=Depends(get_db)):
    """Get full details of a single temple by id."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:

        cur.execute("""
            SELECT t.*, l.state
            FROM temples t
            LEFT JOIN location l ON t.postal_code = l.postal_code
            WHERE t.id = %s
        """, (temple_id,))
        row = cur.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Temple not found")

        cur.execute("""
            SELECT contact_type, value FROM temple_contact WHERE temple_id = %s
        """, (temple_id,))
        contacts = cur.fetchall()

        cur.execute("""
            SELECT day, hours FROM temple_hours WHERE temple_id = %s
        """, (temple_id,))
        hours = cur.fetchall()

    return build_temple(row, contacts, hours)